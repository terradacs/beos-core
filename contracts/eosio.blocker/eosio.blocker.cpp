/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */

#include "eosio.blocker.hpp"

#include <eosiolib/action.hpp>
#include <eosiolib/currency.hpp>
#include <eosio.token/eosio.token.hpp>

using eosio::print;
using eosio::name;
using std::string;

namespace eosio {

using eosio::currency;

void blocker::add_account( account_name account, bool from )
{
   if( from )
   {
      valid_senders_type senders( _self, _self );
      auto found = senders.find( account );
      if( found == senders.end() )
            senders.emplace( _self, [&]( auto& a ){
               a.account = account;
            });
   }
   else
   {
      valid_recip_type recipients( _self, _self );
      auto found = recipients.find( account );
      if( found == recipients.end() )
            recipients.emplace( _self, [&]( auto& a ){
               a.account = account;
            });
   }
}

void blocker::remove_account( account_name account, bool from )
{
   if( from )
   {
      valid_senders_type senders( _self, _self );
      auto found = senders.find( account );
      if( found != senders.end() )
         senders.erase( found );
   }
   else
   {
      valid_recip_type recipients( _self, _self );
      auto found = recipients.find( account );
      if( found != recipients.end() )
         recipients.erase( found );
   }
}

void blocker::update( account_name account, bool from, bool insert )
{
   require_auth( _self );

   if( insert )
      add_account( account, from );
   else
      remove_account( account, from );
}

bool blocker::is_valid() const
{
   auto data = unpack_action_data<currency::transfer>();

   //Issuer of given coin must be the same as owner of `blocker` contract.
   bool owner_of_asset = eosio::token( N(eosio.token) ).get_issuer( data.quantity.symbol.name() ) == _self;
   if( !owner_of_asset )
      return true;

   valid_senders_type senders( _self, _self );
   valid_recip_type recipients( _self, _self );

   bool result_from = senders.find( data.from ) != senders.end();
   bool result_to = recipients.find( data.to ) != recipients.end();

   return result_from || result_to;
}

} /// namespace eosio

extern "C" {
   void apply( uint64_t receiver, uint64_t code, uint64_t action ) {
      auto self = receiver;
      if( action == N(onerror)) {
         /* onerror is only valid if it is for the "eosio" code account and authorized by "eosio"'s "active permission */
         eosio_assert(code == N(eosio), "onerror action's are only valid from the \"eosio\" system account");
      }
      if( code == self || action == N(onerror) ) {
         eosio::blocker thiscontract( self );
         switch( action ) {
            EOSIO_API( eosio::blocker, (update) )
         }
         /* does not allow destructor of thiscontract to run: eosio_exit(0); */
      }
      else if( code == N(eosio.token) && action == N(transfer) )
      {
         eosio::blocker thiscontract( self );

         bool is_valid = thiscontract.is_valid();

         string info = "transfer is blocked by " + name{ receiver }.to_string() + " contract";
         eosio_assert( is_valid, info.c_str() );
      }
   }
}
