#include <eosio/chain/voting_manager.hpp>

#include <eosio/chain/config.hpp>
#include <eosio/chain/controller.hpp>
#include <eosio/chain/database_utils.hpp>
#include <eosio/chain/exceptions.hpp>

namespace eosio {
namespace chain {

const int64_t  min_activated_stake = 150'000'000'0000;

static constexpr uint32_t seconds_per_day = 24 * 3600;

using voting_manager_index_set = index_set<
   voter_info_index,
   global_vote_stat_index
>;

fc::mutable_variant_object voter_info_object::convert_to_public_voter_info() const
   {
   return mutable_variant_object()
      ("owner", owner)
      ("proxy", proxy)
      ("producers", producers)
      ("staked", staked)
      ("last_vote_weight", last_vote_weight)
      ("proxied_vote_weight", proxied_vote_weight)
      ("is_proxy", is_proxy)
      ("reserved1", reserved1)
      ("reserved2", reserved2)
      ("reserved3", reserved3)
      ;
   }

void voting_manager::add_indices()
   {
   voting_manager_index_set::add_indices(_db);
   }

void voting_manager::initialize_database()
   {
   const auto& defaultStat = _db.create<global_vote_stat_object>([](global_vote_stat_object& ) {});
   }

void voting_manager::add_to_snapshot(const snapshot_writer_ptr& snapshot) const
   {
   voting_manager_index_set::walk_indices([this, &snapshot](auto utils) {
      snapshot->write_section<typename decltype(utils)::index_t::value_type>([this](auto& section) {
         decltype(utils)::walk(_db, [this, &section](const auto &row) {
            section.add_row(row, _db);
            });
         });
      });
   }

void voting_manager::read_from_snapshot(const snapshot_reader_ptr& snapshot)
   {
   voting_manager_index_set::walk_indices([this, &snapshot](auto utils) {
      snapshot->read_section<typename decltype(utils)::index_t::value_type>([this](auto& section) {
         bool more = !section.empty();
         while(more) {
            decltype(utils)::create(_db, [this, &section, &more](auto &row) {
               more = section.read_row(row, _db);
               });
            }
         });
      });

   }

void voting_manager::get_voting_stats(int64_t* total_activated_stake, uint64_t* thresh_activated_stake_time,
   double* total_producer_vote_weight) const
   {
   const auto& defaultStatObject = _db.get<global_vote_stat_object>(0);
   *total_activated_stake = defaultStatObject.total_activated_stake;
   *thresh_activated_stake_time = defaultStatObject.thresh_activated_stake_time;
   *total_producer_vote_weight = defaultStatObject.total_producer_vote_weight;
   }

void voting_manager::store_voting_stats(int64_t total_activated_stake, uint64_t thresh_activated_stake_time,
   double total_producer_vote_weight)
   {
   const auto& defaultStatObject = _db.get<global_vote_stat_object>(0);

   _db.modify<global_vote_stat_object>(defaultStatObject,
      [total_activated_stake, thresh_activated_stake_time, total_producer_vote_weight](global_vote_stat_object& obj) {
         obj.thresh_activated_stake_time = thresh_activated_stake_time;
         obj.total_activated_stake = total_activated_stake;
         obj.total_producer_vote_weight = total_producer_vote_weight;
      }
      );
   }

inline double voting_manager::get_producer_vote_weight() const
   {
   const auto& defaultStatObject = _db.get<global_vote_stat_object>(0);
   return defaultStatObject.total_producer_vote_weight;
   }

inline void voting_manager::set_producer_vote_weight(double w)
   {
   const auto& defaultStatObject = _db.get<global_vote_stat_object>(0);

   _db.modify<global_vote_stat_object>(defaultStatObject,
      [w](global_vote_stat_object& obj) {
      obj.total_producer_vote_weight = w;
      }
   );
   }

void voting_manager::register_voting_proxy(const account_name& proxy, bool isproxy,
   const producer_info_index& _producers)
   {
   const auto& _voters = _db.get_index<voter_info_index, by_owner>();
   auto& writableVoters = _db.get_mutable_index<voter_info_index>();

   auto pitr = _voters.find(proxy);
   if(pitr != _voters.end()) {
      eosio_assert(isproxy != pitr->is_proxy, "action has no effect");
      eosio_assert(!isproxy || !pitr->proxy, "account that uses a proxy is not allowed to become a proxy");
      writableVoters.modify(*pitr, [&](auto& p) {
         p.is_proxy = isproxy;
         });
      propagate_weight_change(*pitr,  _producers);
      }
   else {
      writableVoters.emplace([&](auto& p) {
         p.owner = proxy;
         p.is_proxy = isproxy;
         });
      }
   }

void voting_manager::propagate_weight_change(const voter_info_object& voter, const producer_info_index& _producers)
   {
   const auto& _voters = _db.get_index<voter_info_index, by_owner>();
   auto& writableVoters = _db.get_mutable_index<voter_info_index>();

   eosio_assert(voter.proxy.empty() || !voter.is_proxy, "account registered as a proxy is not allowed to use a proxy");
   double new_weight = stake2vote(voter.staked);
   if(voter.is_proxy) {
      new_weight += voter.proxied_vote_weight;
      }

   /// don't propagate small changes (1 ~= epsilon)
   if(fabs(new_weight - voter.last_vote_weight) > 1) {
      if(voter.proxy) {
         auto foundProxyI = _voters.find(voter.proxy);
         eosio_assert(foundProxyI != _voters.end(), "proxy not found"); //data corruption
         const auto& proxy = *foundProxyI; 
         writableVoters.modify(proxy, [&](auto& p) {
            p.proxied_vote_weight += new_weight - voter.last_vote_weight;
            }
         );
         propagate_weight_change(proxy, _producers);
         }
      else {
         auto delta = new_weight - voter.last_vote_weight;
         auto total_producer_vote_weight = get_producer_vote_weight();

         for(auto acnt : voter.producers) {
            auto pitr = _producers.find(acnt); 
            eosio_assert(pitr != _producers.end(), "producer not found"); //data corruption
            pitr->second->total_votes += delta;
            total_producer_vote_weight += delta;
            }

         set_producer_vote_weight(total_producer_vote_weight);
         }
      }
   
   writableVoters.modify(voter, [&](auto& v) {
      v.last_vote_weight = new_weight;
      }
   );

   }

void voting_manager::update_voting_power(const account_name& from, int64_t stake_delta,
   const producer_info_index& _producers)
   {
   const auto& voters = _db.get_index<voter_info_index, by_owner>();
   auto& writableVoters = _db.get_mutable_index<voter_info_index>();

   const voter_info_object* foundVoterInfo = nullptr;

   auto from_voter = voters.find(from);
   if(from_voter == voters.end())
      {
      foundVoterInfo = &writableVoters.emplace(
         [&from, stake_delta](auto& v)
            {
               v.owner = from;
               v.staked = stake_delta;
            }
         );
      }
   else
      {
      foundVoterInfo = &(*from_voter);
      writableVoters.modify(*from_voter, [&stake_delta](auto& v) {
         v.staked += stake_delta;
         });
      }
   
   eosio_assert(0 <= foundVoterInfo->staked, "stake for voting cannot be negative");

   if(from == N(b1))
      validate_b1_vesting(foundVoterInfo->staked);

   if(foundVoterInfo->producers.empty() == false || foundVoterInfo->proxy)
      update_votes(from, foundVoterInfo->proxy, foundVoterInfo->producers, false, _producers);
   }

void voting_manager::update_votes(const account_name& voter_name, const account_name& proxy,
   const std::vector<account_name>& producers, bool voting, const producer_info_index& _producers)
   {
   const auto& _voters = _db.get_index<voter_info_index, by_owner>();
   auto& writableVoters = _db.get_mutable_index<voter_info_index>();

   auto voter = _voters.find(voter_name);
   eosio_assert(voter != _voters.end(), "user must stake before they can vote"); /// staking creates voter object
   eosio_assert(!proxy || !voter->is_proxy, "account registered as a proxy is not allowed to use a proxy");

   int64_t total_activated_stake = 0; uint64_t thresh_activated_stake_time = 0;
   double total_producer_vote_weight = 0;

   get_voting_stats(&total_activated_stake, &thresh_activated_stake_time, &total_producer_vote_weight);

   /**
   * The first time someone votes we calculate and set last_vote_weight, since they cannot unstake until
   * after total_activated_stake hits threshold, we can use last_vote_weight to determine that this is
   * their first vote and should consider their stake activated.
   */
   if(voter->last_vote_weight <= 0.0) {
      total_activated_stake += voter->staked;
      if(total_activated_stake >= min_activated_stake && thresh_activated_stake_time == 0) {
         thresh_activated_stake_time = current_time();
         }
      }

   auto new_vote_weight = stake2vote(voter->staked);
   if(voter->is_proxy) {
      new_vote_weight += voter->proxied_vote_weight;
      }

   boost::container::flat_map<account_name, pair<double, bool /*new*/> > producer_deltas;
   if(voter->last_vote_weight > 0) {
      if(voter->proxy) {
         auto old_proxy = _voters.find(voter->proxy);
         eosio_assert(old_proxy != _voters.end(), "old proxy not found"); //data corruption
         writableVoters.modify(*old_proxy, [&](auto& vp) {
            vp.proxied_vote_weight -= voter->last_vote_weight;
            });
         
         store_voting_stats(total_activated_stake, thresh_activated_stake_time, total_producer_vote_weight);
         propagate_weight_change(*old_proxy, _producers);
         }
      else {
         for(const auto& p : voter->producers) {
            auto& d = producer_deltas[p];
            d.first -= voter->last_vote_weight;
            d.second = false;
            }
         }
      }

   if(proxy) {
      auto new_proxy = _voters.find(proxy);
      eosio_assert(new_proxy != _voters.end(), "invalid proxy specified"); //if ( !voting ) { data corruption } else { wrong vote }
      eosio_assert(!voting || new_proxy->is_proxy, "proxy not found");
      if(new_vote_weight >= 0) {
         writableVoters.modify(*new_proxy, [&](auto& vp) {
            vp.proxied_vote_weight += new_vote_weight;
            });

         store_voting_stats(total_activated_stake, thresh_activated_stake_time, total_producer_vote_weight);
         propagate_weight_change(*new_proxy, _producers);
         }
      }
   else {
      if(new_vote_weight >= 0) {
         for(const auto& p : producers) {
            auto& d = producer_deltas[p];
            d.first += new_vote_weight;
            d.second = true;
            }
         }
      }

   for(const auto& pd : producer_deltas) {
      auto pitr = _producers.find(pd.first);
      if(pitr != _producers.end()) {
         eosio_assert(!voting || pitr->second->is_active || !pd.second.second /* not from new set */, "producer is not currently registered");
            pitr->second->total_votes += pd.second.first;
            if(pitr->second->total_votes < 0) { // floating point arithmetics can give small negative numbers
               pitr->second->total_votes = 0;
               }
            
            total_producer_vote_weight += pd.second.first;
            //eosio_assert( p.total_votes >= 0, "something bad happened" );
         }
      else {
         eosio_assert(!pd.second.second /* not from new set */, "producer is not registered"); //data corruption
         }
      }

   store_voting_stats(total_activated_stake, thresh_activated_stake_time, total_producer_vote_weight);

   writableVoters.modify(*voter, [&](auto& av) {
      av.last_vote_weight = new_vote_weight;
      av.producers = producers;
      av.proxy = proxy;
      });
   }

const voter_info_object* voting_manager::find_voter_info(const account_name& name) const
   {
   const auto* voter = _db.find<voter_info_object, by_owner>(name);
   return voter;
   }

void voting_manager::process_voters(const account_name& lowerBound, const account_name& upperBound, voter_processor processor) const
   {
   const auto& idx = _db.get_index<voter_info_index, by_owner>();

   auto lbI = lowerBound.empty() ? idx.begin() : idx.lower_bound(lowerBound);
   auto ubI = upperBound.empty() ? idx.end() : idx.lower_bound(upperBound);

   bool canContinue = true;
   for(; canContinue && lbI != ubI; ++lbI)
      {
      const voter_info_object& v = *lbI;
      auto nextI = lbI;
      ++nextI;
      bool hasNext = nextI != ubI; 
      canContinue = processor(v, hasNext);
      }
   }

inline uint64_t voting_manager::current_time() const {
   return static_cast<uint64_t>(_controller.pending_block_time().time_since_epoch().count());
   }

inline void voting_manager::validate_b1_vesting(int64_t stake) const
   {
   const int64_t base_time = 1527811200; /// 2018-06-01
   const int64_t max_claimable = 100'000'000'0000ll;
   const uint32_t seconds_per_year = 52 * 7 * 24 * 3600;
   const int64_t claimable = int64_t(max_claimable * double(now() - base_time) / (10 * seconds_per_year));

   eosio_assert(max_claimable - claimable <= stake, "b1 can only claim their tokens over 10 years");
   }

inline double voting_manager::stake2vote(int64_t staked) const {
   /// TODO subtract 2080 brings the large numbers closer to this decade
   double weight = int64_t((now() - (config::block_timestamp_epoch / 1000)) / (seconds_per_day * 7)) / double(52);
   return double(staked) * std::pow(2, weight);
   }

inline void voting_manager::eosio_assert(bool condition, const char* msg) const
   {
   if(BOOST_UNLIKELY(!condition)) {
      std::string message(msg);
      edump((message));
      EOS_THROW(eosio_assert_message_exception, "assertion failure with message: ${s}", ("s", message));
      }
   }

} } /// namespace eosio::chain

