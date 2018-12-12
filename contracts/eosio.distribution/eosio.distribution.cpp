
#include "eosio.distribution.hpp"
#include <eosio.init/eosio.init.hpp>
#include <eosio.token/eosio.token.hpp>
#include <eosio.system/eosio.system.hpp>

namespace eosio {

//This method is triggered every block.
void distribution::onblock( uint32_t block_nr ) {
   bool distribute_beos = block_nr == _gstate.beos.next_block;
   bool distribute_ram = block_nr == _gstate.ram.next_block;
   if ( !(distribute_beos|distribute_ram) )
      return;

   int64_t distrib_ram_bytes=0, distrib_net_weight=0, distrib_cpu_weight=0;
   get_resource_limits( _self, &distrib_ram_bytes, &distrib_net_weight, &distrib_cpu_weight );
   eosio_assert(distrib_ram_bytes > 0 && distrib_net_weight >= 0 && distrib_cpu_weight >= 0,
      "initresource not called properly on beos.distrib");

   uint64_t beos_to_distribute = 0;
   uint64_t beos_to_distribute_trustee = 0;
   uint64_t ram_to_distribute = 0;
   uint64_t ram_to_distribute_trustee = 0;

   if ( distribute_beos ) {
      // set next beos distribution block (leave on current if this one is last)
      _gstate.beos.next_block += _gstate.beos.block_interval;
      if ( !is_within_beos_distribution_period(_gstate.beos.next_block) )
         _gstate.beos.next_block = block_nr;
      // calculate value of user/trustee beos rewards for current distribution
      beos_to_distribute = static_cast<uint64_t>(distrib_net_weight); //beos.distrib holds all rewards on net weight
        //ABW: for perfect safety we should actually subtract all resources beos.distrib might currently have
        //as borrowed, however since no account can call delegatebw until end of distribution, we can assume
        //there is no borrowed bandwidth
      beos_to_distribute -= static_cast<uint64_t>(distrib_cpu_weight); //make sure beos.distrib has leftover
        //resources (otherwise it won't be even possible to call changeparams); leftover size is defined by stake in cpu
      calculate_current_reward( &beos_to_distribute, &beos_to_distribute_trustee, block_nr, _gstate.beos );
   }
   if ( distribute_ram ) {
      // set next ram distribution block (leave on current if this one is last)
      _gstate.ram.next_block += _gstate.ram.block_interval;
      if ( !is_within_ram_distribution_period(_gstate.ram.next_block) )
         _gstate.ram.next_block = block_nr;
      // calculate value of user/trustee ram rewards for current distribution
      uint64_t used_ram = static_cast<uint64_t>(get_account_ram_usage(_self));
      if (used_ram < _gstate.ram_leftover)
         used_ram = _gstate.ram_leftover;
      ram_to_distribute = static_cast<uint64_t>(distrib_ram_bytes) - used_ram;
      calculate_current_reward( &ram_to_distribute, &ram_to_distribute_trustee, block_nr, _gstate.ram );
   }

   // execute actual distribution
   eosiosystem::immutable_system_contract sc(N(eosio));
   eosiosystem::eosio_voting_data vud = sc.prepare_data_for_voting_update();
   eosio::print("Distributing @block ", block_nr, " bandwidth ", beos_to_distribute, " (", beos_to_distribute_trustee,
      "), ram ", ram_to_distribute, " (", ram_to_distribute_trustee, ")\n");
   reward_all( beos_to_distribute, beos_to_distribute_trustee, ram_to_distribute, ram_to_distribute_trustee,
      _gstate.proxy_assets.data(), _gstate.proxy_assets.size(), vud.producer_infos.data(), vud.producer_infos.size() );

   INLINE_ACTION_SENDER(eosiosystem::system_contract, updateprods)( N(eosio), {N(eosio),N(active)},{ vud } );

   // reduce total trustee reward by values rewarded above
   _gstate.beos.trustee_reward -= beos_to_distribute_trustee;
   _gstate.ram.trustee_reward -= ram_to_distribute_trustee;

   // save corrected variables in permanent state
   _global.set( _gstate, _self );

   // finish distribution if this was last block
   if ( _gstate.beos.next_block <= block_nr && _gstate.ram.next_block <= block_nr )
      reward_done();
}

void distribution::calculate_current_reward( uint64_t* to_distribute, uint64_t* to_distribute_trustee,
      uint32_t block_nr, const distribution_parameters& params ) {
   *to_distribute_trustee = params.trustee_reward;
   if ( *to_distribute_trustee > *to_distribute )
      *to_distribute_trustee = *to_distribute;
   *to_distribute -= *to_distribute_trustee;
   uint32_t remaining_distribution_steps = (params.ending_block - block_nr) / params.block_interval + 1;
   *to_distribute /= remaining_distribution_steps;
   *to_distribute_trustee /= remaining_distribution_steps;
}

void distribution::changeparams( distrib_global_state new_params ) {
   require_auth( _self );
   new_params.beos.next_block = new_params.beos.starting_block;
   new_params.ram.next_block = new_params.ram.starting_block;

   check( new_params );

   _gstate = new_params;
   _global.set( _gstate, _self );
}

void distribution::storeparams(uint32_t )
{
  require_auth( _self );

  auto tmp = _global.exists() ? _global.get() : get_default_parameters();
  _global.set( tmp, _self );
}

} /// namespace eosio

EOSIO_ABI( eosio::distribution, (onblock)(changeparams)(storeparams) )
