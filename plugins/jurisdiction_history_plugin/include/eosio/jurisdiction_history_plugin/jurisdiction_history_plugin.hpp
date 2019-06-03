#pragma once
#include <appbase/application.hpp>
#include <eosio/chain_plugin/chain_plugin.hpp>
#include <eosio/chain/types.hpp>
#include <eosio/chain/jurisdiction_object.hpp>
#include <sqlite3.h>

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

        struct producer_jurisdiction_history_object
        {
          chain::account_name producer;
          uint64_t block_number;
          fc::time_point date_changed;
          std::vector<chain::code_jurisdiction> new_jurisdictions;
        };

        struct get_producer_jurisdiction_for_block_results
        {
          producer_jurisdiction_history_object producer_jurisdiction_for_block;
        };

        struct get_producer_jurisdiction_history_params
        {
          chain::account_name producer;
          fc::time_point from_date;
          fc::time_point to_date;
        };

        struct get_producer_jurisdiction_history_results
        {
          std::vector<producer_jurisdiction_history_object> producer_jurisdiction_history;
        };

        get_producer_jurisdiction_for_block_results get_producer_jurisdiction_for_block(const get_producer_jurisdiction_for_block_params &params);
        get_producer_jurisdiction_history_results get_producer_jurisdiction_history(const get_producer_jurisdiction_history_results &params);

        void on_producer_jurisdiction_change(const chain::account_name &producer, uint64_t block_number, fc::time_point date_changed, std::vector<chain::code_jurisdiction> &new_jurisdictions);

        read_write(sqlite3 *db) : db(db) {}
        ~read_write();
        
      private:
        sqlite3 *db;
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

        jurisdiction_apis::read_write get_read_write_api() const;

      private:
        sqlite3 *db;
        std::unique_ptr<class jurisdiction_history_plugin_impl> my;
  };
}
