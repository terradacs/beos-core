#pragma once
#include <appbase/application.hpp>
#include <eosio/chain_plugin/chain_plugin.hpp>
#include <eosio/chain/types.hpp>
#include <set>
#include <eosio/chain/jurisdiction_object.hpp>

namespace eosio {
  namespace jurisdiction_apis
  {
    constexpr uint16_t JURISDICTION_QUERY_LIMIT = 1000;

    class read_only
    {
      public:
        struct get_producer_jurisdiction_params
        {
          std::vector<std::string> producer_names;
        };

        struct producer_jurisdiction_api_object
        {
          chain::account_name producer;
          std::vector<chain::code_jurisdiction> jurisdictions;

          producer_jurisdiction_api_object(const chain::account_name &producer, const std::vector<chain::code_jurisdiction> &jurisdictions) :
            producer(producer),
            jurisdictions(jurisdictions)
          {

          }
        };

        struct get_producer_jurisdiction_results
        {
          std::vector<producer_jurisdiction_api_object> producer_jurisdictions;
        };

        struct get_active_jurisdictions_params
        {
          uint16_t limit = JURISDICTION_QUERY_LIMIT;
        };

        struct get_active_jurisdictions_results
        {
          std::set<chain::code_jurisdiction> jurisdictions;
        };

        struct get_all_jurisdictions_params
        {
          uint16_t limit = JURISDICTION_QUERY_LIMIT;
          fc::optional<chain::code_jurisdiction> last_code;
        };

        struct jurisdiction_api_dictionary_object
        {
          chain::code_jurisdiction code;
          std::string name;
          std::string description;

          jurisdiction_api_dictionary_object(const chain::jurisdiction_dictionary_object &jdo) :
            code(jdo.code),
            name(jdo.name.c_str()),
            description(jdo.description.c_str())
          {

          }
        };

        struct get_all_jurisdictions_results
        {
          std::vector<jurisdiction_api_dictionary_object> jurisdictions;
        };

        read_only(const controller& db, const fc::microseconds& abi_serializer_max_time) : 
          db( db ), 
          abi_serializer_max_time( abi_serializer_max_time ) 
        {

        }

        get_producer_jurisdiction_results get_producer_jurisdiction(const get_producer_jurisdiction_params &prod_jur_params);
        get_active_jurisdictions_results get_active_jurisdictions(const get_active_jurisdictions_params &params);
        get_all_jurisdictions_results get_all_jurisdictions(const get_all_jurisdictions_params &all_jur_params);

    private:
      const controller& db;
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

        jurisdiction_apis::read_only get_read_only_api() const;

      private:
        std::unique_ptr<class jurisdiction_plugin_impl> my;
  };
}

FC_REFLECT(eosio::jurisdiction_apis::read_only::producer_jurisdiction_api_object, (producer)(jurisdictions));
FC_REFLECT(eosio::jurisdiction_apis::read_only::get_producer_jurisdiction_params, (producer_names));
FC_REFLECT(eosio::jurisdiction_apis::read_only::get_producer_jurisdiction_results, (producer_jurisdictions));

FC_REFLECT(eosio::jurisdiction_apis::read_only::get_active_jurisdictions_params, (limit));
FC_REFLECT(eosio::jurisdiction_apis::read_only::get_active_jurisdictions_results, (jurisdictions));

FC_REFLECT(eosio::jurisdiction_apis::read_only::jurisdiction_api_dictionary_object, (code)(name)(description));
FC_REFLECT(eosio::jurisdiction_apis::read_only::get_all_jurisdictions_params, (limit)(last_code));
FC_REFLECT(eosio::jurisdiction_apis::read_only::get_all_jurisdictions_results, (jurisdictions));
