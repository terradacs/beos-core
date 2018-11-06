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

namespace eosio {

   class distribution : public contract {

      private:

        using ConstModifier = std::function< void( const init_data& a )>;

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
   };

} /// namespace eosio
