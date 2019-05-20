#pragma once
#include <eosio/jurisdiction_plugin/jurisdiction_plugin.hpp>
#include <eosio/chain_plugin/chain_plugin.hpp>
#include <eosio/http_plugin/http_plugin.hpp>

#include <appbase/application.hpp>

namespace eosio {
   class jurisdiction_api_plugin : public plugin<jurisdiction_api_plugin> {
      public:
        APPBASE_PLUGIN_REQUIRES((jurisdiction_plugin)(chain_plugin)(http_plugin))

        jurisdiction_api_plugin();
        virtual ~jurisdiction_api_plugin();

        virtual void set_program_options(options_description&, options_description&) override;

        void plugin_initialize(const variables_map&);
        void plugin_startup();
        void plugin_shutdown();
   };
}