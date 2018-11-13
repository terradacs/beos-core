
#include "eosio.distribution.hpp"
#include <eosio.token/eosio.token.hpp>
#include <eosio.system/eosio.system.hpp>
#include <eosio.gateway/eosio.gateway.hpp>

namespace eosio {

distribution::distribution( account_name self )
          : contract( self )
{
}

distribution::~distribution()
{
}

void distribution::execute( uint32_t block_nr, asset proxy_asset,
  uint32_t starting_block_for_any_distribution, uint32_t ending_block_for_any_distribution,
  uint32_t distribution_payment_block_interval_for_any_distribution, uint64_t amount_of_reward,
  uint64_t amount_of_reward_for_trustee, bool is_beos_mode )
{
  //Only during a distribution period, an action can be called.
  if( block_nr >= starting_block_for_any_distribution && block_nr <= ending_block_for_any_distribution )
    {
      //Maintenance period.
      if( ( ( block_nr - starting_block_for_any_distribution ) % distribution_payment_block_interval_for_any_distribution ) == 0 )
      {
        //Rewarding all accounts.
        uint64_t gathered_amount = get_sum();

        reward_all( amount_of_reward, amount_of_reward_for_trustee, gathered_amount, &proxy_asset, sizeof(asset), is_beos_mode );

        //Total end of distribution period. Transferring from staked BEOS/RAM to liquid BEOS/RAM.
        //It depends on `is_beos_mode` variable.
        if(
            ( block_nr == ending_block_for_any_distribution ) ||
            ( block_nr + distribution_payment_block_interval_for_any_distribution > ending_block_for_any_distribution )
          )
        {
          reward_done( &proxy_asset, sizeof(asset), is_beos_mode );
        }
      }
    }
}

//This method is triggered every block.
void distribution::onblock( uint32_t block_nr )
{
  eosio::beos_global_state b_state = eosio::init( N(beos.init) ).get_beos_global_state();

  //Rewarding staked BEOSes, issuing BEOSes.
  execute( block_nr, b_state.proxy_asset, b_state.beos.starting_block_for_distribution, b_state.beos.ending_block_for_distribution,
    b_state.beos.distribution_payment_block_interval_for_distribution, b_state.beos.amount_of_reward, b_state.trustee.amount_of_reward,
    true/*is_beos_mode*/ );

  //Rewarding staked RAM, buying RAM.
  execute( block_nr, b_state.proxy_asset, b_state.ram.starting_block_for_distribution, b_state.ram.ending_block_for_distribution,
    b_state.ram.distribution_payment_block_interval_for_distribution, b_state.ram.amount_of_reward, 0, false/*is_beos_mode*/ );
}

uint64_t distribution::get_sum()
{
  eosio::beos_global_state b_state = eosio::init( N(beos.init) ).get_beos_global_state();
  auto issued = eosio::token( N(eosio.token) ).get_supply( b_state.proxy_asset.symbol.name() ).amount;
  auto withdrawn = eosio::token( N(eosio.token) ).check_balance( N(beos.gateway), b_state.proxy_asset.symbol ).amount;
  
  eosio_assert( issued >= withdrawn, "issued PXBTS >= withdrawn PXBTS" );

  return issued - withdrawn;
}

} /// namespace eosio

EOSIO_ABI( eosio::distribution, (onblock) )
