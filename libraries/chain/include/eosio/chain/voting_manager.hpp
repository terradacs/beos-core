#pragma once

#include <eosio/chain/snapshot.hpp>
#include <eosio/chain/types.hpp>
#include <eosio/chain/asset.hpp>

#include <chainbase/chainbase.hpp>

#include "multi_index_includes.hpp"

#include <eosiolib/block_producer_voting_info.hpp>

#include <fc/variant_object.hpp>

#include <functional>
#include <vector>

namespace eosio {
namespace chain {

class controller;
struct controller_impl;

struct voter_info_object : public chainbase::object<voter_info_object_type, voter_info_object> {
   
   OBJECT_CTOR(voter_info_object)

   id_type                     id;

   account_name                owner = 0; /// the voter
   account_name                proxy = 0; /// the proxy set by the voter, if any
   std::vector<account_name>   producers; /// the producers approved by this voter if no proxy set
   int64_t                     staked = 0;

   /**
   *  Every time a vote is cast we must first "undo" the last vote weight, before casting the
   *  new vote weight.  Vote weight is calculated as:
   *
   *  stated.amount * 2 ^ ( weeks_since_launch/weeks_per_year)
   */
   double                      last_vote_weight = 0; /// the vote weight cast the last time the vote was updated

                                                     /**
                                                     * Total vote weight delegated to this voter.
                                                     */
   double                      proxied_vote_weight = 0; /// the total vote weight delegated to this voter as a proxy
   bool                        is_proxy = 0; /// whether the voter is a proxy for others


   uint32_t                    reserved1 = 0;
   uint32_t                    reserved2 = 0;
   asset                       reserved3;

   fc::mutable_variant_object  convert_to_public_voter_info() const;
};

struct by_owner;

using voter_info_index = chainbase::shared_multi_index_container<
   voter_info_object,
   indexed_by<
      ordered_unique<tag<by_id>, member<voter_info_object, voter_info_object::id_type, &voter_info_object::id>>,
      ordered_unique<tag<by_owner>, member<voter_info_object, account_name, &voter_info_object::owner>>
      >
   >;

struct global_vote_stat_object : chainbase::object<global_vote_stat_object_type, global_vote_stat_object> {
   
   OBJECT_CTOR(global_vote_stat_object)

   id_type id;
   int64_t total_activated_stake = 0;
   uint64_t thresh_activated_stake_time = 0;
   double total_producer_vote_weight = 0;
};

using global_vote_stat_index = chainbase::shared_multi_index_container<
   global_vote_stat_object,
   indexed_by<
   ordered_unique<tag<by_id>, member<global_vote_stat_object, global_vote_stat_object::id_type, &global_vote_stat_object::id>>
   >
>;

/// Helper class to delegate functionality related to storing voter-data from huge priviledged_api class.
class voting_manager final
   {
   public:
      typedef boost::container::flat_map<account_name, block_producer_voting_info*> producer_info_index;

      /// Allows to retrieve data related to eosio.system stats which are also modified during voting process, thus stored at native side.
      void get_voting_stats(int64_t* total_activated_stake, uint64_t* thresh_activated_stake_time,
         double* total_producer_vote_weight) const;

      void store_voting_stats(int64_t total_activated_stake, uint64_t thresh_activated_stake_time,
         double total_producer_vote_weight);

      /** Implements registration/unregistration of vote account proxy.
          It's a part of system_contract::regproxy implementation and underlying priviledged_api::register_voting_proxy.
      */
      void register_voting_proxy(const account_name& proxy, bool is_proxy,
         const producer_info_index& _producers);

      /** Allows to update given account voting power according to specified stake change.
          Actual implementation of priviledged_api::update_voting_power.
      */
      void update_voting_power(const account_name& voter, int64_t stake_delta,
         const producer_info_index& _producers);

      void update_votes(const account_name& voter_name, const account_name& proxy,
         const std::vector<account_name>& producers, bool voting,
         const producer_info_index& _producers);

      const voter_info_object* find_voter_info(const account_name& name) const;

      typedef std::function<bool(const voter_info_object&, bool)> voter_processor;

      /** Allows to process all entries included in `by_owner` index range <lowerBound, upperBound).
          \param lowerBound lower bound of the query to start iteration from,
          \param upperBound upper bound of the query to end iteration,
          \param processor - processing lambda, which shall return false to stop iteration. Takes arguments: 
               const voter_info_object& voter - entry to be processed,
               bool hasNext - true if there is available next item during iteration.
      */
      void process_voters(const account_name& lowerBound, const account_name& upperBound, voter_processor processor) const;

      void set_min_activated_stake(int64_t _min_activated_stake)
         { min_activated_stake = _min_activated_stake; }

      int64_t get_min_activated_stake() const { return min_activated_stake; }

   private:
      friend struct eosio::chain::controller_impl;
      /// Can be instantiated only by controller.
      voting_manager(controller& c, chainbase::database& d) : _controller(c), _db(d) {}

      void add_indices();
      void initialize_database();
      void add_to_snapshot(const snapshot_writer_ptr& snapshot) const;
      void read_from_snapshot(const snapshot_reader_ptr& snapshot);

   private:
      double get_producer_vote_weight() const;
      void set_producer_vote_weight(double w);

      void propagate_weight_change(const voter_info_object& voter, const producer_info_index& _producers);

      uint64_t current_time() const;
      /**
      *  Returns the time in seconds from 1970 of the block including this action
      *  @brief Get time (rounded down to the nearest second) of the current block (i.e. the block including this action)
      *  @return time in seconds from 1970 of the current block
      */
      uint32_t  now() const {
         return (uint32_t)(current_time() / 1000000);
      }

      void validate_b1_vesting(int64_t stake) const;
      double stake2vote(int64_t staked) const;

      void eosio_assert(bool condition, const char* msg) const;

   /// Class data:
   private:
      controller& _controller;
      chainbase::database& _db;
      int64_t  min_activated_stake = std::numeric_limits<int64_t>::max();
   };

} }

FC_REFLECT(eosio::chain::voter_info_object, (owner)(proxy)(producers)(staked)(last_vote_weight)(proxied_vote_weight)
                                            (is_proxy)(reserved1)(reserved2)(reserved3)
          )

FC_REFLECT(eosio::chain::global_vote_stat_object, (total_activated_stake)(thresh_activated_stake_time)(total_producer_vote_weight))

CHAINBASE_SET_INDEX_TYPE(eosio::chain::voter_info_object, eosio::chain::voter_info_index)
CHAINBASE_SET_INDEX_TYPE(eosio::chain::global_vote_stat_object, eosio::chain::global_vote_stat_index)
