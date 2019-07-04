/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */

#include "eosio.system.hpp"

#include <eosio.token/eosio.token.hpp>

namespace eosiosystem {

   void system_contract::addjurisdict( account_name ram_payer, code_jurisdiction new_code, std::string new_name, std::string new_description )
   {
      eosio::print("Entering system_contract::addjurisdict\n");
      require_auth( ram_payer );

      eosio_assert( new_name.size() < limit_256, "size of name is greater than allowed" );
      eosio_assert( new_description.size() < limit_256, "size of description is greater than allowed" );

      size_t size = action_data_size();
      std::unique_ptr<char, decltype(&free)> buffer( reinterpret_cast<char*>( malloc( size ) ), &free );
      read_action_data( buffer.get(), size );
      add_jurisdiction( buffer.get(), size );

      if( ram_payer != _self )
      {
         //Preventing against spamming
         INLINE_ACTION_SENDER(eosio::token, transfer)( N(eosio.token), {ram_payer,N(active)},
                                                         { ram_payer, _gstate.jurisdiction_fee_receiver, _gstate.jurisdiction_fee, "jurisdiction fee" } );
      }
      eosio::print("Leaving system_contract::addjurisdict\n");
   }

   void system_contract::updateprod( eosio::jurisdiction_producer data )
   {
      eosio::print( ( "Entering system_contract::updateprod for producer: " + name{ data.producer }.to_string() + "\n" ).c_str() );
      require_auth( data.producer );

      eosio_assert( data.jurisdictions.size() < limit_256, "number of jurisdictions is greater than allowed" );

      typedef eosio::multi_index< N(producers), eosiosystem::producer_info > producer_info_t;
      producer_info_t _producers( N(eosio), N(eosio) );

      auto _found_producer = _producers.find( data.producer );
      eosio_assert( _found_producer != _producers.end(), "user is not a producer" );

      size_t size = action_data_size();
      std::unique_ptr<char, decltype(&free)> buffer( reinterpret_cast<char*>( malloc( size ) ), &free );
      read_action_data( buffer.get(), size );
      update_jurisdictions( buffer.get(), size );

      eosio::print("Leaving system_contract::updateprod\n");
   }

} //namespace eosiosystem
