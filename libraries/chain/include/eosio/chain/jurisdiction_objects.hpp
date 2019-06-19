#pragma once

#include <eosio/chain/types.hpp>
#include <eosio/chain/producer_schedule.hpp>
#include <eosio/chain/transaction.hpp>
#include <eosio/chain/jurisdiction_object.hpp>
#include <eosio/chain/transaction_metadata.hpp>

#include <fc/static_variant.hpp>

namespace eosio { namespace chain {

using trx_extensions = fc::static_variant< jurisdiction_basic >;

struct trx_extensions_visitor
{
   typedef void result_type;

   const std::vector< char >& _buffer;

   mutable jurisdiction_basic jurisdiction;

   trx_extensions_visitor( const std::vector< char >& buffer );

   void operator()( const jurisdiction_basic& _jurisdiction ) const;
};

class jurisdiction_provider_interface : public std::enable_shared_from_this< jurisdiction_provider_interface >
{
   public:

      using ptr_base = std::shared_ptr< jurisdiction_provider_interface >;

   public:

      jurisdiction_provider_interface(){}
      virtual ~jurisdiction_provider_interface(){}

      ptr_base getptr();

      virtual void update( const account_name& producer ) = 0;
      virtual fc::optional< jurisdiction_producer > get_jurisdiction_producer() = 0;
};

class jurisdiction_base_provider : public jurisdiction_provider_interface
{
   public:

      using ptr_base = std::shared_ptr< jurisdiction_base_provider >;

   private:

      using data_container = std::map< account_name, jurisdiction_producer >;

      account_name active_producer;
      data_container data;

   public:

      jurisdiction_base_provider(){}
      ~jurisdiction_base_provider() override{}

      void update( const account_name& new_producer ) override;
      fc::optional< jurisdiction_producer > get_jurisdiction_producer() override;

      void change( const jurisdiction_producer& src );
};

using jurisdiction_test_provider = jurisdiction_base_provider;
using jurisdiction_gps_provider  = jurisdiction_base_provider;

class jurisdiction_action_launcher
{
   public:

      using ptr_provider = std::shared_ptr< jurisdiction_provider_interface >;
      using signature_provider_type = std::function<chain::signature_type(chain::digest_type)>;

   private:

      bool producer_changed = false;

      account_name active_producer;
      signature_provider_type signature_provider;

      ptr_provider provider;

      void update_provider();
      fc::optional< jurisdiction_producer > get_jurisdiction_producer();

      bool is_equal( const chainbase::database &db, const jurisdiction_producer& src );

   public:

      const account_name& get_active_producer() const;

      void set_provider( ptr_provider new_provider );

      void update( account_name new_producer, const signature_provider_type& new_signature_provider = signature_provider_type() );

      transaction_metadata_ptr get_jurisdiction_transaction( const chainbase::database &db, const block_id_type& block_id, const time_point& time, const chain::chain_id_type& chain_id );
      void set_inactive_producer();

      static bool check_jurisdictions( const chainbase::database &db, const jurisdiction_producer_ordered& src );
};

class jurisdiction_manager
{
   private:

      template< typename T >
      using jurisdiction_processor = std::function<bool(const T&, bool)>;

   public:
   
      static const uint16_t limit_256;
      static const char* too_many_jurisdictions_exception;

      using jurisdictions = std::vector< jurisdiction_basic >;

      using jurisdiction_dictionary_processor = jurisdiction_processor< jurisdiction_dictionary_object >;
      using jurisdiction_producer_processor = jurisdiction_processor< jurisdiction_producer_object >;

   private:

      uint16_t read( uint16_t idx, const std::vector< char >& buffer, std::vector< jurisdiction_basic >& dst );

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
