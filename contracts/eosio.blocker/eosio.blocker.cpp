/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */

#include "eosio.blocker.hpp"

#include <eosiolib/action.hpp>
#include <eosiolib/currency.hpp>

using eosio::print;
using eosio::name;
using std::string;

namespace eosio {

using eosio::currency;

void blocker::update( account_name account, bool from, bool insert )
{
   require_auth( _self );

   if( insert )
   {
      if( from )
      {
         from_accounts_type from_accounts( _self, _self );
         auto found = from_accounts.find( account );
         if( found == from_accounts.end() )
               from_accounts.emplace( _self, [&]( auto& a ){
                  a.account = account;
               });
      }
      else
      {
         to_accounts_type to_accounts( _self, _self );
         auto found = to_accounts.find( account );
         if( found == to_accounts.end() )
               to_accounts.emplace( _self, [&]( auto& a ){
                  a.account = account;
               });
      }
   }
   else
   {
      if( from )
      {
         from_accounts_type from_accounts( _self, _self );
         auto found = from_accounts.find( account );
         if( found != from_accounts.end() )
            from_accounts.erase( found );
      }
      else
      {
         to_accounts_type to_accounts( _self, _self );
         auto found = to_accounts.find( account );
         if( found != to_accounts.end() )
            to_accounts.erase( found );
      }
   }
}

bool blocker::is_valid() const
{
   auto data = unpack_action_data<currency::transfer>();

   to_accounts_type to_accounts( _self, _self );
   from_accounts_type from_accounts( _self, _self );

   bool result_from = from_accounts.find( data.from ) != from_accounts.end();
   bool result_to = to_accounts.find( data.to ) != to_accounts.end();

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
