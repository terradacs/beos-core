
#include "eosio.distribution.hpp"
#include <eosio.init/eosio.init.hpp>
#include <eosio.token/eosio.token.hpp>
#include <eosio.system/eosio.system.hpp>

namespace eosio {

//This method is triggered every block.
void distribution::onblock( uint32_t block_nr ) {
   bool distribute_beos = false, distribute_beos_late = false, distribute_ram = false, distribute_ram_late = false;
   if ( !is_past_beos_distribution_period(block_nr) ) {
      distribute_beos = block_nr == _gstate.beos.next_block;
      distribute_beos_late = block_nr > _gstate.beos.next_block;
      if ( distribute_beos_late ) {
         // last scheduled beos distribution block failed
         // reschedule to next block or try now if next block would be past end of distribution
         _gstate.beos.next_block += _gstate.beos.block_interval;
         if ( is_past_beos_distribution_period(_gstate.beos.next_block) || _gstate.beos.next_block == block_nr) {
            _gstate.beos.next_block = block_nr;
            eosio::print("Last bandwidth distribution transaction failed. Retrying now.\n");
            distribute_beos = true;
         } else {
            eosio::print("Last bandwidth distribution transaction failed. Setting retry @block ", _gstate.beos.next_block, "\n");
         }
      }
   }
   if ( !is_past_ram_distribution_period(block_nr) ) {
      distribute_ram = block_nr == _gstate.ram.next_block;
      distribute_ram_late = block_nr > _gstate.ram.next_block;
      if ( distribute_ram_late ) {
         // last scheduled ram distribution block failed
         // reschedule to next block or try now if next block would be past end of distribution
         _gstate.ram.next_block += _gstate.ram.block_interval;
         if ( is_past_ram_distribution_period(_gstate.ram.next_block || _gstate.ram.next_block == block_nr) ) {
            _gstate.ram.next_block = block_nr;
            eosio::print("Last ram distribution transaction failed. Retrying now.\n");
            distribute_ram = true;
         } else {
            eosio::print("Last ram distribution transaction failed. Setting retry @block ", _gstate.ram.next_block, "\n");
         }
      }
   }

   if ( !(distribute_beos|distribute_ram) ) {
      if (distribute_beos_late|distribute_ram_late)
         _global.set( _gstate, _self );
      return;
   }

   int64_t distrib_ram_bytes=0, distrib_net_weight=0, distrib_cpu_weight=0;
   get_resource_limits( _self, &distrib_ram_bytes, &distrib_net_weight, &distrib_cpu_weight );
   eosio_assert(distrib_ram_bytes > 0 && distrib_net_weight >= 0 && distrib_cpu_weight >= 0,
      "initresource not called properly on beos.distrib");

   uint64_t beos_to_distribute = 0;
   uint64_t beos_to_distribute_trustee = 0;
   uint64_t ram_to_distribute = 0;
   uint64_t ram_to_distribute_trustee = 0;

   if ( distribute_beos ) {
      // set next beos distribution block
      _gstate.beos.next_block += _gstate.beos.block_interval;
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
      // set next ram distribution block
      _gstate.ram.next_block += _gstate.ram.block_interval;
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
   if ( is_past_beos_distribution_period(_gstate.beos.next_block) && is_past_ram_distribution_period(_gstate.ram.next_block) )
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

void distribution::check( const distribution_parameters& state, uint32_t current_block ) {
   //distribution must be wholly in the future or in the past (to effectively disable it)
   eosio_assert( state.starting_block > current_block || state.ending_block < current_block,
      "Starting block already passed" );
   eosio_assert( state.ending_block >= state.starting_block, "Distribution period must not be empty" );
   eosio_assert( state.block_interval > 0, "Distribution block interval must be positive value" );
   }

void distribution::check_and_calculate_parameters(distrib_global_state* state) {
   state->beos.next_block = state->beos.starting_block;
   state->ram.next_block = state->ram.starting_block;

   uint32_t block_no = get_blockchain_block_number();
   check( state->beos, block_no );
   check( state->ram, block_no );
   
   if (state->ram_leftover > 0) {
      int64_t distrib_ram_bytes, distrib_net_weight, distrib_cpu_weight;
      get_resource_limits( _self, &distrib_ram_bytes, &distrib_net_weight, &distrib_cpu_weight );
      eosio_assert( static_cast<uint64_t>(distrib_ram_bytes) > state->ram_leftover, "Cannot request to leave more than allocated ram" );
   }

   if (state->proxy_assets.empty())
      return;

   bool calculate_weights = state->proxy_assets.front().amount == 0;
   auto precision_depth = state->proxy_assets.front().symbol.precision();
   for (auto& proxy : state->proxy_assets) {
      eosio_assert( eosio::token( N(eosio.token) ).get_issuer(proxy.symbol.name()) == N(beos.gateway), "Proxy assets must be created with beos.gateway as issuer" );
      eosio_assert( calculate_weights == (proxy.amount == 0) , "All assets need positive weight or all must be 0" );
      if (calculate_weights) {
         auto precision = proxy.symbol.precision();
         if (precision > precision_depth)
            precision_depth = precision;
      } else {
         eosio_assert( proxy.amount > 0, "Asset weight cannot be negative" );
      }
   }
   
   if (calculate_weights) {
      for (auto& proxy : state->proxy_assets) {
         proxy.amount = 1;
         int difference = static_cast<int>( precision_depth - proxy.symbol.precision() );
         for (int i = 0; i < difference; ++i)
            proxy.amount *= 10;
      }
   }
}

void distribution::changeparams( distrib_global_state new_params ) {
   require_auth( _self );

   check_and_calculate_parameters( &new_params );

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
