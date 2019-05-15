/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */
#pragma once

#include <eosiolib/eosio.hpp>

#include <string>

namespace eosio {

   using std::string;

   static constexpr uint8_t max_jurisdictions = 10;

   struct info_jurisdiction
   {
      code_jurisdiction    code;
      std::string          name;

      uint64_t primary_key()const { return code; }

      EOSLIB_SERIALIZE( info_jurisdiction, (code)(name) )
   };

   typedef eosio::multi_index< N(infojurisdic), info_jurisdiction >  info_jurisdiction_table;

   class jurisdiction : public contract {
      private:

         info_jurisdiction_table info_jurisdictions;

      public:

         jurisdiction( account_name self )
         : contract( self ), info_jurisdictions( self, self )
         {
         }

         void addjurisdict( account_name ram_payer, code_jurisdiction new_code, std::string new_name );

         void updateprod( account_name producer, std::vector< code_jurisdiction > new_jurisdictions );
   };

} /// namespace eosio
