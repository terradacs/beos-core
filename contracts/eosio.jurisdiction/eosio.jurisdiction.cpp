/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */

#include "eosio.jurisdiction.hpp"

#include <eosio.system/eosio.system.hpp>

namespace eosio {

   void jurisdiction::addjurisdict( account_name ram_payer, code_jurisdiction new_code, std::string new_name )
   {
      require_auth( ram_payer );

      auto found = info_jurisdictions.find( new_code );

      eosio_assert( found == info_jurisdictions.end(), "jurisdiction with the same code exists" );

      info_jurisdictions.emplace( ram_payer, [&]( auto& obj )
      {
         obj.code = new_code;
         obj.name = new_name;
      } );
   }

   void jurisdiction::updateprod( account_name producer, std::vector< code_jurisdiction > new_jurisdictions )
   {
      eosio::print("Entering jurisdiction::updateprod\n");
      require_auth( producer );

      eosio_assert( new_jurisdictions.size() <= max_jurisdictions, "number of jurisdictions is greater than allowed" );

      typedef eosio::multi_index< N(producers), eosiosystem::producer_info > producer_info_t;
      producer_info_t _producers( N(eosio), N(eosio) );

      //I don't know if to check presence of producer
      //auto _found_producer = _producers.find( producer );
      //eosio_assert( _found_producer != _producers.end(), "user is not a producer" );

      for( auto item : new_jurisdictions )
         eosio_assert( info_jurisdictions.find( item ) != info_jurisdictions.end(), "jurisdiction doesn't exist" );

      constexpr size_t max_stack_buffer_size = 512;
      size_t size = action_data_size();
      char* buffer = (char*)( max_stack_buffer_size < size ? malloc(size) : alloca(size) );
      read_action_data( buffer, size );
      update_jurisdictions( buffer, size );

      eosio::print("Leaving jurisdiction::updateprod\n");
   }

} /// namespace eosio

EOSIO_ABI( eosio::jurisdiction, (addjurisdict)(updateprod) )
