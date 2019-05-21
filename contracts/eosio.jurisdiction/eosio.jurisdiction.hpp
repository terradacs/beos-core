/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */
#pragma once

#include <eosiolib/eosio.hpp>

#include <string>

namespace eosio {

   static constexpr uint16_t limit_256 = 256;
   static constexpr uint32_t jurisdiction_fee = 100 * 1024;//100KB RAM

   struct info_jurisdiction
   {
      code_jurisdiction    code;
      std::string          name;
      std::string          description;

      uint64_t primary_key()const { return code; }
      uint64_t get_key_name()const { return ::eosio::string_to_name( name.c_str() ); }

      EOSLIB_SERIALIZE( info_jurisdiction, (code)(name)(description) )
   };

   typedef eosio::multi_index< N(infojurisdic), info_jurisdiction,
                               indexed_by<N(infonamejuri), const_mem_fun<info_jurisdiction, uint64_t, &info_jurisdiction::get_key_name>  >
                             >  info_jurisdiction_table;

   class jurisdiction : public contract {
      private:

         info_jurisdiction_table info_jurisdictions;

         bool is_unique( const std::string& new_name );

      public:

         jurisdiction( account_name self )
         : contract( self ), info_jurisdictions( self, self )
         {
         }

         void addjurisdict( account_name ram_payer, code_jurisdiction new_code, std::string new_name, std::string new_description );

         void updateprod( account_name producer, std::vector< code_jurisdiction > new_jurisdictions );
   };

} /// namespace eosio
