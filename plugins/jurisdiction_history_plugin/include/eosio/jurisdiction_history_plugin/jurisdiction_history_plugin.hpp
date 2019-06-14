#pragma once
#include <appbase/application.hpp>
#include <eosio/chain_plugin/chain_plugin.hpp>
#include <eosio/chain/jurisdiction_history_object.hpp>

namespace eosio 
{
  namespace jurisdiction_history_apis
  {
    class read_write
    {
      public:
        struct get_producer_jurisdiction_for_block_params
        {
          chain::account_name producer;
          uint64_t block_number;
        };

        struct jurisdiction_history_api_object
        {
          chain::account_name producer_name;
          uint64_t block_with_last_change;
          fc::time_point date_changed;
          std::vector<chain::code_jurisdiction> new_jurisdictions;

          jurisdiction_history_api_object(){}

          jurisdiction_history_api_object(const chain::jurisdiction_history_object &jho) :
            producer_name(jho.producer_name),
            block_with_last_change(jho.block_number),
            date_changed(jho.date_changed)
          {
            new_jurisdictions.assign(jho.new_jurisdictions.begin(), jho.new_jurisdictions.end());
          }
        };

        struct get_producer_jurisdiction_for_block_results
        {
          std::vector<jurisdiction_history_api_object> producer_jurisdiction_for_block;
        };

        struct get_producer_jurisdiction_history_params
        {
          chain::account_name producer;
          fc::optional<fc::time_point> from_date;
          fc::optional<fc::time_point> to_date;
        };

        struct get_producer_jurisdiction_history_results
        {
          std::vector<jurisdiction_history_api_object> producer_jurisdiction_history;
        };

        get_producer_jurisdiction_for_block_results get_producer_jurisdiction_for_block(const get_producer_jurisdiction_for_block_params &params);
        get_producer_jurisdiction_history_results get_producer_jurisdiction_history(const get_producer_jurisdiction_history_params &params);

        read_write(controller& db, const fc::microseconds& abi_serializer_max_time) : 
          db(db), 
          abi_serializer_max_time( abi_serializer_max_time ) 
        {

        }

        ~read_write()
        {

        }

      private:
        controller& db;
        const fc::microseconds abi_serializer_max_time;
    };
  }

  class jurisdiction_history_plugin : public appbase::plugin<jurisdiction_history_plugin>
  {
    public:
      jurisdiction_history_plugin();
      virtual ~jurisdiction_history_plugin();

      APPBASE_PLUGIN_REQUIRES((chain_plugin))
      virtual void set_program_options(options_description& cli, options_description& cfg) override;

      void plugin_initialize(const variables_map& options);
      void plugin_startup();
      void plugin_shutdown();

      jurisdiction_history_apis::read_write get_read_write_api() const;

    private:
      std::unique_ptr<class jurisdiction_history_plugin_impl> my;
  };
}

FC_REFLECT(eosio::jurisdiction_history_apis::read_write::get_producer_jurisdiction_for_block_params, (producer)(block_number));
FC_REFLECT(eosio::jurisdiction_history_apis::read_write::jurisdiction_history_api_object, (producer_name)(block_with_last_change)(date_changed)(new_jurisdictions));
FC_REFLECT(eosio::jurisdiction_history_apis::read_write::get_producer_jurisdiction_for_block_results, (producer_jurisdiction_for_block));
FC_REFLECT(eosio::jurisdiction_history_apis::read_write::get_producer_jurisdiction_history_params, (producer)(from_date)(to_date));
FC_REFLECT(eosio::jurisdiction_history_apis::read_write::get_producer_jurisdiction_history_results, (producer_jurisdiction_history));
