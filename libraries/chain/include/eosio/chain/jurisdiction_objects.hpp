#pragma once

#include <eosio/chain/types.hpp>
#include <eosio/chain/producer_schedule.hpp>

#include <fc/static_variant.hpp>

namespace eosio { namespace chain {

struct trx_jurisdiction
{
   std::vector< code_jurisdiction >	jurisdictions;
};

using trx_extensions = fc::static_variant< trx_jurisdiction >;

struct trx_extensions_visitor
{
   typedef void result_type;

   const std::vector< char >& _buffer;

   mutable trx_jurisdiction jurisdiction;

   trx_extensions_visitor( const std::vector< char >& buffer );

   void operator()( const trx_jurisdiction& _trx_jurisdiction ) const;
};

class jurisdiction_helper
{
   public:
   
      using jurisdictions = std::vector< trx_jurisdiction >;

   private:

      void read( uint16_t idx, const std::vector< char >& buffer, std::vector< trx_jurisdiction >& dst );

   public:

      jurisdictions read( const extensions_type& exts );

      bool update( chainbase::database& db, const jurisdiction_updater_ordered& updater );
};

} }  // eosio::chain

FC_REFLECT( eosio::chain::trx_jurisdiction, (jurisdictions) )
