/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */
#pragma once

#include "voter_info.hpp"

#include <eosio.system/native.hpp>
#include <eosiolib/asset.hpp>
#include <eosiolib/time.hpp>
#include <eosiolib/privileged.hpp>
#include <eosiolib/singleton.hpp>
#include <eosiolib/block_producer_voting_info.hpp>

#include <eosio.system/exchange_state.hpp>

#include <string>
#include <vector>

namespace eosiosystem {

   using eosio::asset;
   using eosio::indexed_by;
   using eosio::const_mem_fun;
   using eosio::block_timestamp;

   struct name_bid {
     account_name            newname;
     account_name            high_bidder;
     int64_t                 high_bid = 0; ///< negative high_bid == closed auction waiting to be claimed
     uint64_t                last_bid_time = 0;

     auto     primary_key()const { return newname;                          }
     uint64_t by_high_bid()const { return static_cast<uint64_t>(-high_bid); }
   };

   typedef eosio::multi_index< N(namebids), name_bid,
                               indexed_by<N(highbid), const_mem_fun<name_bid, uint64_t, &name_bid::by_high_bid>  >
                               >  name_bid_table;


   struct eosio_global_state : eosio::blockchain_parameters {
      uint64_t free_ram()const { return max_ram_size - total_ram_bytes_reserved; }

      uint64_t             max_ram_size = 64ll*1024 * 1024 * 1024;
      uint64_t             total_ram_bytes_reserved = 0;
      int64_t              total_ram_stake = 0;

      block_timestamp      last_producer_schedule_update;
      uint64_t             last_pervote_bucket_fill = 0;
      int64_t              pervote_bucket = 0;
      int64_t              perblock_bucket = 0;
      uint32_t             total_unpaid_blocks = 0; /// all blocks which have been produced but not paid
      int64_t              total_activated_stake = 0;
      uint64_t             thresh_activated_stake_time = 0;
      uint16_t             last_producer_schedule_size = 0;
      double               total_producer_vote_weight = 0; /// the sum of all producer votes
      uint32_t             total_producers = 0;
      block_timestamp      last_name_close;

      account_name         jurisdiction_fee_receiver = N(eosio.null);
      asset                jurisdiction_fee = asset( 1000 * 10000 );

      // explicit serialization macro is not necessary, used here only to improve compilation time
      EOSLIB_SERIALIZE_DERIVED( eosio_global_state, eosio::blockchain_parameters,
                                (max_ram_size)(total_ram_bytes_reserved)(total_ram_stake)
                                (last_producer_schedule_update)(last_pervote_bucket_fill)
                                (pervote_bucket)(perblock_bucket)(total_unpaid_blocks)(total_activated_stake)(thresh_activated_stake_time)
                                (last_producer_schedule_size)(total_producer_vote_weight)(total_producers)(last_name_close)
                                (jurisdiction_fee_receiver)(jurisdiction_fee) )
   };

   struct producer_info {
      account_name          owner;
      double                total_votes = 0;
      eosio::public_key     producer_key; /// a packed public key object
      bool                  is_active = true;
      std::string           url;
      uint32_t              unpaid_blocks = 0;
      uint64_t              last_claim_time = 0;
      uint16_t              location = 0;

      uint64_t primary_key()const { return owner;                                   }
      double   by_votes()const    { return is_active ? -total_votes : total_votes;  }
      bool     active()const      { return is_active;                               }
      void     deactivate()       { producer_key = public_key(); is_active = false; }

      // explicit serialization macro is not necessary, used here only to improve compilation time
      EOSLIB_SERIALIZE( producer_info, (owner)(total_votes)(producer_key)(is_active)(url)
                        (unpaid_blocks)(last_claim_time)(location) )
   };

   typedef eosio::multi_index< N(producers), producer_info,
                               indexed_by<N(prototalvote), const_mem_fun<producer_info, double, &producer_info::by_votes>  >
                               >  producers_table;

   typedef eosio::singleton<N(global), eosio_global_state> global_state_singleton;

   //   static constexpr uint32_t     max_inflation_rate = 5;  // 5% annual inflation
   static constexpr uint32_t     seconds_per_day = 24 * 3600;
   static constexpr uint64_t     system_token_symbol = CORE_SYMBOL;

   static constexpr uint16_t limit_256 = 256;
   static constexpr uint32_t jurisdiction_fee = 100 * 1024;//100KB RAM

   class immutable_system_contract : public native
      {
      public:

         using jurisdiction_info_type = std::pair< account_name, asset >;

      protected:

         producers_table         _producers;

         global_state_singleton  _global;
         eosio_global_state      _gstate;

         inline std::vector<block_producer_voting_info> prepare_producer_infos( uint32_t total_producers ) const
         {
            return std::vector<block_producer_voting_info>( total_producers );
         }

      public:
         immutable_system_contract(account_name s)
         : native(s), _producers(_self, _self), _global(_self,_self) {}

         std::vector<block_producer_voting_info> prepare_data_for_voting_update()
         {
            uint32_t total_producers = 0;

            if( _global.exists() )
            {
               _gstate = _global.get();
               total_producers = _gstate.total_producers;
            }

            return prepare_producer_infos( total_producers );
         }

      };

   class system_contract : public immutable_system_contract {
      private:

         rammarket              _rammarket;

         int64_t                _min_activated_stake = std::numeric_limits<int64_t>::max();
         uint32_t               _min_activated_stake_percent = 100; // it is only for print message properly

      public:
         system_contract( account_name s );
         ~system_contract();

         // Actions:
         /**
          *  Create initial issue of CORE_SYMBOL and evaluate and set min_activated_stake.
          */
         void initialissue( uint64_t quantity, uint8_t min_activated_stake_percent );

         void onblock( block_timestamp timestamp, account_name producer );
                      // const block_header& header ); /// only parse first 3 fields of block header

         // functions defined in delegate_bandwidth.cpp

         /**
          *  Stakes SYS from the balance of 'from' for the benfit of 'receiver'.
          *  If transfer == true, then 'receiver' can unstake to their account
          *  Else 'from' can unstake at any time.
          */
         void delegatebw( account_name from, account_name receiver,
                          asset stake_net_quantity, asset stake_cpu_quantity, bool transfer );


         /**
          *  Decreases the total tokens delegated by from to receiver and/or
          *  frees the memory associated with the delegation if there is nothing
          *  left to delegate.
          *
          *  This will cause an immediate reduction in net/cpu bandwidth of the
          *  receiver.
          *
          *  A transaction is scheduled to send the tokens back to 'from' after
          *  the staking period has passed. If existing transaction is scheduled, it
          *  will be canceled and a new transaction issued that has the combined
          *  undelegated amount.
          *
          *  The 'from' account loses voting power as a result of this call and
          *  all producer tallies are updated.
          */
         void undelegatebw( account_name from, account_name receiver,
                            asset unstake_net_quantity, asset unstake_cpu_quantity );


         /**
          * Increases receiver's ram quota based upon current price and quantity of
          * tokens provided. An inline transfer from receiver to system contract of
          * tokens will be executed.
          */
         void buyram( account_name buyer, account_name receiver, asset tokens );
         void buyrambytes( account_name buyer, account_name receiver, uint32_t bytes );

         /**
          *  Reduces quota my bytes and then performs an inline transfer of tokens
          *  to receiver based upon the average purchase price of the original quota.
          */
         void sellram( account_name receiver, int64_t bytes );

         /**
          *  This action is called after the delegation-period to claim all pending
          *  unstaked tokens belonging to owner
          */
         void refund( account_name owner );

         // functions defined in voting.cpp

         void regproducer( const account_name producer, const public_key& producer_key, const std::string& url, uint16_t location );

         void unregprod( const account_name producer );

         void setram( uint64_t max_ram_size );

         void voteproducer( const account_name voter, const account_name proxy, const std::vector<account_name>& producers );

         void updateprods( const std::vector<block_producer_voting_info>& producer_infos );

         void regproxy( const account_name proxy, bool isproxy );

         void setparams( const eosio::blockchain_parameters& params );

         // functions defined in producer_pay.cpp
         void claimrewards( const account_name& owner );

         void setpriv( account_name account, uint8_t ispriv );

         void rmvproducer( account_name producer );

         void bidname( account_name bidder, account_name newname, asset bid );

         /**
          *  Turns unlimited account resource(s) into concrete limit(s) by buying ram / staking.
          *  Pass -1 to leave particular limit unchanged (-1 will not change limited resource back into unlimited!).
          *  eosio is payer, so it has to have enough liquid tokens for the operation.
          */
         void initresource( account_name receiver, int64_t bytes, int64_t stake_net_quantity, int64_t stake_cpu_quantity );

         void defineprods(std::vector<eosio::producer_key> schedule);

         bool is_allowed_vote_operation() const;
         bool is_allowed_ram_operation() const;

         void addjurisdict( account_name ram_payer, code_jurisdiction new_code, std::string new_name, std::string new_description );
         void updateprod( eosio::jurisdiction_producer data );

      private:
         void update_elected_producers( block_timestamp timestamp );

         // Implementation details:

         //defind in delegate_bandwidth.cpp
         void changebw( account_name from, account_name receiver,
                        asset stake_net_quantity, asset stake_cpu_quantity, bool transfer );

         //defined in voting.hpp
         static eosio_global_state get_default_parameters();
         void update_votes( const account_name voter, const account_name proxy, const std::vector<account_name>& producers, bool voting );
         void update_voting_power(const account_name voter, int64_t stake_delta);
         void flush_voting_stats();

   };

} /// eosiosystem
