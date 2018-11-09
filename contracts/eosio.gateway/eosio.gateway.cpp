/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */

#include "eosio.gateway.hpp"

#include <eosio.token/eosio.token.hpp>
#include <eosio.system/eosio.system.hpp>
#include <beoslib/beos_privileged.hpp>

namespace eosio {

void gateway::issue( account_name to, asset quantity )
{
  auto from = N(beos.gateway);

  eosio_assert( from != to, "cannot issue to self" );
  require_auth( from );

  require_recipient( from );
  require_recipient( to );

  //Check if token exists at all.
  asset token_supply = eosio::token(N(eosio.token)).get_supply( quantity.symbol.name() );

  eosio_assert( quantity.is_valid(), "invalid quantity" );
  eosio_assert( quantity.amount > 0, "must issue positive quantity" );
  eosio_assert( quantity.symbol == token_supply.symbol, "symbol precision mismatch" );

  /*
    There are 3 cases:
    a) only issue
    b) only transfer
    c) issue + transfer
  */
  auto gateway_balance = eosio::token( N(eosio.token) ).check_balance( from, quantity.symbol );

  if( gateway_balance.amount == 0 )//a
  {
    //Sending PROXY to the user `to` during every lock.
    INLINE_ACTION_SENDER(eosio::token, issue)( N(eosio.token), {{from,N(active)}},
                                            { to, quantity, std::string("issue - distribution period")} );
  }
  else if( gateway_balance >= quantity )//b
  {
    INLINE_ACTION_SENDER(eosio::token, transfer)( N(eosio.token), {from,N(active)},
                                               { from, to, quantity, std::string("transfer - distribution period") } );
  }
  else//c
  {
    INLINE_ACTION_SENDER(eosio::token, transfer)( N(eosio.token), {from,N(active)},
                                               { from, to, gateway_balance, std::string("transfer - distribution period") } );

    quantity -= gateway_balance;
    eosio_assert( quantity.amount > 0, "must issue positive quantity" );
    INLINE_ACTION_SENDER(eosio::token, issue)( N(eosio.token), {{from,N(active)}},
                                            { to, quantity, std::string("issue - distribution period")} );
  }

  add( to, from );
}

void gateway::withdraw( account_name owner, asset quantity )
{
  checker( owner, quantity );

  eosio_assert( quantity.amount > 0, "must withdraw positive quantity" );

  auto balance = eosio::token( N(eosio.token) ).check_balance( owner, quantity.symbol );
  eosio_assert( balance >= quantity, "overdrawn balance during withdraw" );

  INLINE_ACTION_SENDER(eosio::token, transfer)( N(eosio.token), {owner,N(active)},
                                               { owner, N(beos.gateway), quantity, std::string("withdraw") } );
}

void gateway::checker( account_name any_account, asset value )
{
  require_recipient( any_account );
  require_auth( any_account );

  asset token_supply = eosio::token(N(eosio.token)).get_supply( value.symbol.name() );
  eosio_assert( value.symbol == token_supply.symbol, "symbol precision mismatch" );
}

void gateway::add( account_name owner, account_name ram_payer )
{
  inits _init( _self, _self );

  auto itr = _init.find( owner );

  if( itr == _init.end() )
  {
    _init.emplace( ram_payer, [&]( auto& a ){
      a.owner = owner;
    });
  }
}

} /// namespace eosio

EOSIO_ABI( eosio::gateway, (issue)(withdraw) )
