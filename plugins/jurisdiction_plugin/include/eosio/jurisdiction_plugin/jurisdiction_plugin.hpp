#pragma once
#include <appbase/application.hpp>
#include <eosio/chain_plugin/chain_plugin.hpp>
#include <eosio/chain/types.hpp>
#include <set>

namespace eosio {
  namespace jurisdiction_apis
  {
    class read_write
    {
      public:
        struct get_producer_jurisdiction_params
        {
          std::string producer_name;
        };

        struct get_producer_jurisdiction_results
        {
          chain::account_name producer_name;
          std::vector<chain::code_jurisdiction> jurisdictions;
        };

        struct get_active_jurisdictions_results
        {
          std::set<chain::code_jurisdiction> jurisdictions;
        };

        struct get_active_jurisdictions_params
        {

        };

        struct get_all_jurisdictions_params
        {
          chain::name code;
          std::string scope;
        };

        read_write(controller& db, const fc::microseconds& abi_serializer_max_time) : 
          db( db ), 
          abi_serializer_max_time( abi_serializer_max_time ) 
        {

        }

        get_producer_jurisdiction_results get_producer_jurisdiction(const get_producer_jurisdiction_params &producer_name);
        get_active_jurisdictions_results get_active_jurisdictions(const get_active_jurisdictions_params &);
        chain_apis::read_only::get_table_rows_result get_all_jurisdictions(const get_all_jurisdictions_params &p);

    private:
      controller& db;
      const fc::microseconds abi_serializer_max_time;

    };
  }

  class jurisdiction_plugin : public appbase::plugin<jurisdiction_plugin>
  {
      public:
        jurisdiction_plugin();
        virtual ~jurisdiction_plugin();

        APPBASE_PLUGIN_REQUIRES((chain_plugin))
        virtual void set_program_options(options_description& cli, options_description& cfg) override;

        void plugin_initialize(const variables_map& options);
        void plugin_startup();
        void plugin_shutdown();

        jurisdiction_apis::read_write get_read_write_api() const;

      private:
        std::unique_ptr<class jurisdiction_plugin_impl> my;
  };
}

FC_REFLECT(eosio::jurisdiction_apis::read_write::get_producer_jurisdiction_params, (producer_name));
FC_REFLECT(eosio::jurisdiction_apis::read_write::get_producer_jurisdiction_results, (producer_name)(jurisdictions));
FC_REFLECT(eosio::jurisdiction_apis::read_write::get_active_jurisdictions_results, (jurisdictions));
FC_REFLECT(eosio::jurisdiction_apis::read_write::get_active_jurisdictions_params, );
FC_REFLECT(eosio::jurisdiction_apis::read_write::get_all_jurisdictions_params, (code)(scope));