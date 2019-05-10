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

      eosio_assert( found == info_jurisdictions.end(), "jurisdiction with the same name exists" );

      info_jurisdictions.emplace( ram_payer, [&]( auto& obj )
      {
         obj.code = new_code;
         obj.name = new_name;
      } );
   }

   void jurisdiction::updateprod( account_name producer, std::vector< code_jurisdiction > new_jurisdictions )
   {
      require_auth( producer );

      eosio_assert( new_jurisdictions.size() >= max_jurisdictions, "number of jurisdictions is greater than allowed" );

      typedef eosio::multi_index< N(producers), eosiosystem::producer_info > producer_info_t;
      producer_info_t _producers( N(eosio), N(eosio) );

      auto _found_producer = _producers.find( producer );
      eosio_assert( _found_producer == _producers.end(), "user is not a producer" );

      auto found = producer_jurisdictions.find( producer );

      if( found == producer_jurisdictions.end() )
      {
         producer_jurisdictions.emplace( producer, [&]( auto& obj )
         {
            obj.producer = producer;
            obj.jurisdictions = new_jurisdictions;
         } );
      }
      else
      {
         producer_jurisdictions.modify( found, 0, [&]( auto& obj )
         {
            obj.jurisdictions = new_jurisdictions;
         } );
      }
   }

} /// namespace eosio

EOSIO_ABI( eosio::jurisdiction, (addjurisdict)(updateprod) )
