
#include "eosio.distribution.hpp"
#include <eosio.token/eosio.token.hpp>
#include <eosio.system/eosio.system.hpp>
#include <eosio.gateway/eosio.gateway.hpp>

namespace eosio {

distribution::distribution( account_name self )
          : contract( self ),
            _beos_global( _self, _self )
{
  _beos_gstate = _beos_global.exists() ? _beos_global.get() : get_beos_default_parameters();
}

distribution::~distribution()
{
  _beos_global.set( _beos_gstate, _self );
}

beos_global_state distribution::get_beos_default_parameters()
{
  beos_global_state dp;

  dp.proxy_asset = eosio::init(N(beos.init)).get_proxy_asset();

  dp.starting_block_for_initial_witness_election = eosio::init(N(beos.init)).get_starting_block_for_initial_witness_election();

  dp.beos.starting_block_for_distribution = eosio::init(N(beos.init)).get_starting_block_for_beos_distribution();
  dp.beos.ending_block_for_distribution = eosio::init(N(beos.init)).get_ending_block_for_beos_distribution();
  dp.beos.distribution_payment_block_interval_for_distribution = eosio::init(N(beos.init)).get_distribution_payment_block_interval_for_beos_distribution();
  dp.beos.amount_of_reward = eosio::init(N(beos.init)).get_amount_of_reward_beos();

  dp.ram.starting_block_for_distribution = eosio::init(N(beos.init)).get_starting_block_for_ram_distribution();
  dp.ram.ending_block_for_distribution = eosio::init(N(beos.init)).get_ending_block_for_ram_distribution();
  dp.ram.distribution_payment_block_interval_for_distribution = eosio::init(N(beos.init)).get_distribution_payment_block_interval_for_ram_distribution();
  dp.ram.amount_of_reward = eosio::init(N(beos.init)).get_amount_of_reward_ram();

  dp.trustee.starting_block_for_distribution = eosio::init(N(beos.init)).get_starting_block_for_trustee_distribution();
  dp.trustee.ending_block_for_distribution = eosio::init(N(beos.init)).get_ending_block_for_trustee_distribution();
  dp.trustee.distribution_payment_block_interval_for_distribution = eosio::init(N(beos.init)).get_distribution_payment_block_interval_for_trustee_distribution();
  dp.trustee.amount_of_reward = eosio::init(N(beos.init)).get_amount_of_reward_trustee();

  checker( dp );

  return dp;
}

void distribution::checker( const beos_global_state_element& state )
{
  eosio_assert( state.starting_block_for_distribution > 0, "STARTING_BLOCK_FOR_DISTRIBUTION > 0" );
  eosio_assert( state.ending_block_for_distribution > state.starting_block_for_distribution, "ENDING_BLOCK_FOR_DISTRIBUTION > STARTING_BLOCK_FOR_DISTRIBUTION" );
  eosio_assert( state.distribution_payment_block_interval_for_distribution > 0, "DISTRIBUTION_PAYMENT_BLOCK_INTERVAL_FOR_DISTRIBUTION > 0" );
  eosio_assert( state.amount_of_reward > 0, "AMOUNT_OF_REWARD > 0" );
}

//Checking basic dependencies between BEOS parameters.
void distribution::checker( const beos_global_state& state )
{
  eosio_assert( state.starting_block_for_initial_witness_election > 0, "STARTING_BLOCK_FOR_INITIAL_WITNESS_ELECTION > 0" );

  checker( state.beos );
  checker( state.ram );
  checker( state.trustee );
}

void distribution::execute( uint64_t block_nr, asset proxy_asset, uint64_t starting_block_for_any_distribution, uint64_t ending_block_for_any_distribution,
              uint64_t distribution_payment_block_interval_for_any_distribution, uint64_t nr_items, bool is_beos_mode )
{
  //Only during a distribution period, an action can be called.
  if( block_nr >= starting_block_for_any_distribution && block_nr <= ending_block_for_any_distribution )
    {
      //Maintenance period.
      if( ( ( block_nr - starting_block_for_any_distribution ) % distribution_payment_block_interval_for_any_distribution ) == 0 )
      {
        //Rewarding all accounts.
        rewardall( nr_items, proxy_asset, is_beos_mode );

        //Total end of distribution period. Transferring from staked BEOS/RAM to liquid BEOS/RAM.
        //It depends on `is_beos_mode` variable.
        if(
            ( block_nr == ending_block_for_any_distribution ) ||
            ( block_nr + distribution_payment_block_interval_for_any_distribution > ending_block_for_any_distribution )
          )
        {
          rewarddone( proxy_asset, is_beos_mode );
        }
      }
    }
}

//This method is triggered every block.
void distribution::onblock( block_timestamp timestamp, account_name producer )
{
  uint64_t block_nr = static_cast< uint64_t >( get_blockchain_block_number() );

  //Rewarding staked BEOSes, issuing BEOSes.
  execute( block_nr, _beos_gstate.proxy_asset, _beos_gstate.beos.starting_block_for_distribution, _beos_gstate.beos.ending_block_for_distribution,
    _beos_gstate.beos.distribution_payment_block_interval_for_distribution, _beos_gstate.beos.amount_of_reward, true/*is_beos_mode*/ );

  //Rewarding staked RAM, buying RAM.
  execute( block_nr, _beos_gstate.proxy_asset, _beos_gstate.ram.starting_block_for_distribution, _beos_gstate.ram.ending_block_for_distribution,
    _beos_gstate.ram.distribution_payment_block_interval_for_distribution, _beos_gstate.ram.amount_of_reward, false/*is_beos_mode*/ );

}

uint64_t distribution::get_sum()
{
  auto issued = eosio::token( N(eosio.token) ).get_supply( _beos_gstate.proxy_asset.symbol.name() ).amount;
  auto withdrawn = eosio::token( N(eosio.token) ).check_balance( N(beos.gateway), _beos_gstate.proxy_asset.symbol.name() ).amount;
  
  eosio_assert( issued >= withdrawn, "issued PXBTS >= withdrawn PXBTS" );

  return issued - withdrawn;
}

void distribution::rewardall( uint64_t total_amount, asset symbol/*correct symbol of BEOS coin, for example: `0.0000 BEOS`*/, bool is_beos_mode )
{
  //Retrieve total sum of balances for every account.
  uint64_t gathered_amount = get_sum();

  if( gathered_amount == 0 )
    return;

  auto callable = [&]( const init_data& obj )
  {
    auto balance = eosio::token( N(eosio.token) ).check_balance( obj.owner, symbol.symbol.name() );  
    //Calculation ratio for given account.
    long double ratio = static_cast< long double >( balance.amount ) / gathered_amount;
    int64_t val = static_cast< int64_t >( total_amount * ratio );

    if( val > 0 )
    {
      if( is_beos_mode )
      {
        //Staking BEOS for user `obj.owner` always during every reward-time.
        auto from = N(beos.distrib);

        auto stake_net = asset( val / 2 );
        auto stake_cpu = asset( val - stake_net.amount );

        INLINE_ACTION_SENDER(eosiosystem::system_contract, reward)( N(eosio), {N(eosio),N(active)},
        { obj.owner, 0/*ram_bytes*/, stake_net/*net_weight*/, stake_cpu/*cpu_weight*/ } );

      }
      else
      {
        INLINE_ACTION_SENDER(eosiosystem::system_contract, reward)( N(eosio), {N(eosio),N(active)},
        { obj.owner, val/*ram_bytes*/, asset()/*net_weight*/, asset()/*cpu_weight*/ } );
      }
    }

  };

  //Review all accounts
  review( callable );
}

void distribution::rewarddone( asset symbol/*correct symbol of BEOS coin, for example: `0.0000 BEOS`*/, bool is_beos_mode )
{
}

void distribution::review( ConstModifier&& mod )
{
  inits _init( N(beos.gateway), N(beos.gateway) );
  auto itr = _init.begin();

  //Go through all accounts and do specific action `mod`.
  while( itr != _init.end() )
  {
    mod( *itr );
    ++itr;
  }
}

//It is possible to change any parameter at runtime.
void distribution::changeparams( beos_global_state new_params )
{
  require_auth( _self );

  checker( new_params );

  _beos_gstate = new_params;
  _beos_global.set( _beos_gstate, _self );
}

} /// namespace eosio

EOSIO_ABI( eosio::distribution, (onblock)(changeparams) )
