#pragma once

#include <eosio/chain/types.hpp>
#include <eosio/chain/producer_schedule.hpp>
#include <eosio/chain/transaction.hpp>
#include <eosio/chain/jurisdiction_object.hpp>

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
   private:

      template< typename T >
      using jurisdiction_processor = std::function<bool(const T&, bool)>;

   public:
   
      static const uint16_t limit_256;
      static const char* too_many_jurisdictions_exception;

      using jurisdictions = std::vector< trx_jurisdiction >;

      using jurisdiction_dictionary_processor = jurisdiction_processor< jurisdiction_dictionary_object >;
      using jurisdiction_producer_processor = jurisdiction_processor< jurisdiction_producer_object >;

   private:

      uint16_t read( uint16_t idx, const std::vector< char >& buffer, std::vector< trx_jurisdiction >& dst );

   public:

      bool check_jurisdictions( const chainbase::database &db, const jurisdiction_producer_ordered& src );

      jurisdictions read( const extensions_type& exts );

      fc::variant get_jurisdiction( const chainbase::database& db, code_jurisdiction code );

      bool update( chainbase::database& db, const jurisdiction_dictionary& info );
      bool update( chainbase::database& db, const jurisdiction_producer_ordered& updater );

      bool transaction_jurisdictions_match( const chainbase::database& db, account_name actual_producer, const packed_transaction& trx );

      void process_jurisdiction_dictionary( const chainbase::database& db, jurisdiction_dictionary_processor processor ) const;
      void process_jurisdiction_producer( const chainbase::database& db, const account_name& lowerBound, const account_name& upperBound, jurisdiction_producer_processor processor ) const;
};

} }  // eosio::chain

FC_REFLECT( eosio::chain::trx_jurisdiction, (jurisdictions) )
