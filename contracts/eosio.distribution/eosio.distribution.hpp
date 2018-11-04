/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */
#pragma once

#include <eosiolib/asset.hpp>
#include <eosiolib/eosio.hpp>
#include <eosiolib/singleton.hpp>
#include <eosiolib/time.hpp>
#include <beoslib/beos_privileged.hpp>
#include <eosio.init/eosio.init.hpp>
#include <eosio.gateway/eosio.gateway.hpp>

#include <string>

namespace eosio {

   using std::string;

    struct beos_global_state_element
    {
      uint64_t starting_block_for_distribution;
      uint64_t ending_block_for_distribution;
      uint64_t distribution_payment_block_interval_for_distribution;
      uint64_t amount_of_reward;

      EOSLIB_SERIALIZE( beos_global_state_element,

      (starting_block_for_distribution)
      (ending_block_for_distribution)
      (distribution_payment_block_interval_for_distribution)
      (amount_of_reward) )
    };

    struct beos_global_state
    {
      asset proxy_asset;
      uint64_t starting_block_for_initial_witness_election;

      beos_global_state_element beos;
      beos_global_state_element ram;
      beos_global_state_element trustee;

      EOSLIB_SERIALIZE( beos_global_state,

      (proxy_asset)
      (starting_block_for_initial_witness_election)
      (beos)
      (ram)
      (trustee) )
    };

   typedef eosio::singleton<N(beosglobal), beos_global_state> beos_global_state_singleton;

   class distribution : public contract {

      private:

        using ConstModifier = std::function< void( const init_data& a )>;

        beos_global_state            _beos_gstate;
        beos_global_state_singleton  _beos_global;

        beos_global_state get_beos_default_parameters();
        void checker( const beos_global_state_element& state );
        void checker( const beos_global_state& state );

        uint64_t get_sum();
        void review( ConstModifier&& mod );

        void execute( uint64_t block_nr, asset proxy_asset, uint64_t starting_block_for_any_distribution, uint64_t ending_block_for_any_distribution,
              uint64_t distribution_payment_block_interval_for_any_distribution, uint64_t nr_items, bool is_beos_mode );

        void rewardall( uint64_t total_amount, asset symbol/*correct symbol of BEOS coin, for example: `0.0000 BEOS`*/, bool is_beos_mode );
        void rewarddone( asset symbol/*correct symbol of BEOS coin, for example: `0.0000 BEOS`*/, bool is_beos_mode );

      public:

        distribution( account_name self );
        ~distribution();

        void onblock( block_timestamp timestamp, account_name producer );
        void changeparams( beos_global_state new_params );

   };

} /// namespace eosio
