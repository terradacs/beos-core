/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */

#include "eosio.jurisdiction.hpp"

#include <eosio.system/eosio.system.hpp>
#include <eosio.token/eosio.token.hpp>

namespace eosio {

   bool jurisdiction::is_unique( const std::string& new_name )
   {
      uint64_t _found_val = ::eosio::string_to_name( new_name.c_str() );

      const auto idx = info_jurisdictions.get_index< N(infonamejuri) >();
      auto found = idx.find( _found_val );

      while( found != idx.end() && _found_val == found->get_key_name() )
      {
         if( found->name == new_name )
            return false;
         ++found;
      }

      return true;
   }

   void jurisdiction::addjurisdict( account_name ram_payer, code_jurisdiction new_code, std::string new_name, std::string new_description )
   {
      require_auth( ram_payer );

      eosio_assert( new_name.size() < limit_256, "size of name is greater than allowed" );
      eosio_assert( new_description.size() < limit_256, "size of description is greater than allowed" );

      auto _tolower = []( const char& c ) { return std::tolower( c ); };
      std::transform( new_name.begin(), new_name.end(), new_name.begin(), _tolower );

      auto found_code = info_jurisdictions.find( new_code );
      eosio_assert( found_code == info_jurisdictions.end(), "jurisdiction with the same code exists" );

      eosio_assert( is_unique( new_name ), "jurisdiction with the same name exists" );

      info_jurisdictions.emplace( ram_payer, [&]( auto& obj )
      {
         obj.code = new_code;
         obj.name = new_name;
         obj.description = new_description;
      } );

      eosiosystem::immutable_system_contract sc(N(eosio));
      auto jurisdiction_information = sc.get_jurisdiction_information();
      const account_name& jurisdiction_fee_receiver = jurisdiction_information.first;
      const asset& jurisdiction_fee = jurisdiction_information.second;

      //Preventing against spamming
      INLINE_ACTION_SENDER(eosio::token, transfer)( N(eosio.token), {ram_payer,N(active)},
                                                      { ram_payer, jurisdiction_fee_receiver, jurisdiction_fee, "jurisdiction fee" } );
   }

   void jurisdiction::updateprod( account_name producer, std::vector< code_jurisdiction > new_jurisdictions )
   {
      eosio::print("Entering jurisdiction::updateprod\n");
      require_auth( producer );

      eosio_assert( new_jurisdictions.size() < limit_256, "number of jurisdictions is greater than allowed" );

      typedef eosio::multi_index< N(producers), eosiosystem::producer_info > producer_info_t;
      producer_info_t _producers( N(eosio), N(eosio) );

      auto _found_producer = _producers.find( producer );
      eosio_assert( _found_producer != _producers.end(), "user is not a producer" );

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
