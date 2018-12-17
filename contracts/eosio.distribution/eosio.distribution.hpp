/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */
#pragma once

#include <eosiolib/asset.hpp>
#include <eosiolib/eosio.hpp>
#include <eosiolib/singleton.hpp>
#include <eosiolib/time.hpp>
#include <eosiolib/privileged.hpp>
#include <beoslib/beos_privileged.hpp>
#include <eosio.gateway/eosio.gateway.hpp>

namespace eosio {

   struct distribution_parameters
   {
      uint32_t starting_block;
      uint32_t next_block;
      uint32_t ending_block;
      uint32_t block_interval;
      uint64_t trustee_reward;

      EOSLIB_SERIALIZE( distribution_parameters,
         (starting_block)
         (next_block)
         (ending_block)
         (block_interval)
         (trustee_reward) )
   };

   struct distrib_global_state
   {
      distribution_parameters beos;
      distribution_parameters ram;
      std::vector<asset> proxy_assets;
      uint64_t ram_leftover;

      EOSLIB_SERIALIZE( distrib_global_state, (beos)(ram)(proxy_assets)(ram_leftover) )
   };

   typedef eosio::singleton<N(distribstate), distrib_global_state> distrib_global_state_singleton;

   class distribution : public contract {

      private:

         distrib_global_state            _gstate;
         distrib_global_state_singleton  _global;

         void check( const distribution_parameters& state, uint32_t current_block );
         void check_and_calculate_parameters( distrib_global_state* state );

         distrib_global_state get_default_parameters() {
            distrib_global_state dp;
            dp.beos.starting_block = 0;
            dp.beos.next_block = 0;
            dp.beos.ending_block = 0;
            dp.beos.block_interval = 1;
            dp.beos.trustee_reward = 0;
            dp.ram.starting_block = 0;
            dp.ram.next_block = 0;
            dp.ram.ending_block = 0;
            dp.ram.block_interval = 1;
            dp.ram.trustee_reward = 0;
            dp.ram_leftover = 0;
            return dp;
         }

         void calculate_current_reward( uint64_t* to_distribute, uint64_t* to_distribute_trustee,
            uint32_t block_nr, const distribution_parameters& params );

      public:

         distribution( account_name self ) : contract( self ),
            _global( _self, _self )
         {
            _gstate = _global.exists() ? _global.get() : get_default_parameters();
         }

         ~distribution() {}

         void onblock( uint32_t block_nr );
         void changeparams( distrib_global_state new_params );
         void storeparams(uint32_t dummy);

         inline distrib_global_state get_global_state() const {
            return _gstate;
         }

         /// current block is inside [ starting_block : ending_block ] for BEOS distribution
         inline bool is_active_beos_distribution_period() const;
         inline bool is_within_beos_distribution_period( uint32_t block_nr ) const;

         /// current block is above ending_block for BEOS distribution
         inline bool is_past_beos_distribution_period() const;
         inline bool is_past_beos_distribution_period( uint32_t block_nr ) const;

         /// current block is inside [ starting_block : ending_block ] for RAM distribution
         inline bool is_active_ram_distribution_period() const;
         inline bool is_within_ram_distribution_period( uint32_t block_nr ) const;

         /// current block is above ending_block for RAM distribution
         inline bool is_past_ram_distribution_period() const;
         inline bool is_past_ram_distribution_period( uint32_t block_nr ) const;
   };

   inline bool distribution::is_active_beos_distribution_period() const {
      auto block_nr = get_blockchain_block_number();
      return is_within_beos_distribution_period(block_nr);
   }
   
   inline bool distribution::is_within_beos_distribution_period( uint32_t block_nr ) const {
      return _gstate.beos.starting_block <= block_nr && block_nr <= _gstate.beos.ending_block;
   }

   inline bool distribution::is_past_beos_distribution_period() const {
      auto block_nr = get_blockchain_block_number();
      return is_past_beos_distribution_period(block_nr);
   }
   
   inline bool distribution::is_past_beos_distribution_period( uint32_t block_nr ) const {
      return _gstate.beos.ending_block < block_nr;
   }

   inline bool distribution::is_active_ram_distribution_period() const {
      auto block_nr = get_blockchain_block_number();
      return is_within_ram_distribution_period(block_nr);
   }

   inline bool distribution::is_within_ram_distribution_period( uint32_t block_nr ) const {
      return _gstate.ram.starting_block <= block_nr && block_nr <= _gstate.ram.ending_block;
   }

   inline bool distribution::is_past_ram_distribution_period() const {
      auto block_nr = get_blockchain_block_number();
      return is_past_ram_distribution_period(block_nr);
   }

   inline bool distribution::is_past_ram_distribution_period( uint32_t block_nr ) const {
      return _gstate.ram.ending_block < block_nr;
   }

} /// namespace eosio
