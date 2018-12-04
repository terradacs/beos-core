/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */

#pragma once
#include <eosio/test_producer_plugin/test_producer_plugin.hpp>
#include <eosio/chain_plugin/chain_plugin.hpp>
#include <eosio/http_plugin/http_plugin.hpp>

#include <appbase/application.hpp>

namespace eosio {

   using std::unique_ptr;
   using namespace appbase;

   class test_producer_api_plugin : public plugin<test_producer_api_plugin> {
      public:
        APPBASE_PLUGIN_REQUIRES((test_producer_plugin)(chain_plugin)(http_plugin))

        test_producer_api_plugin();
        virtual ~test_producer_api_plugin();

        virtual void set_program_options(options_description&, options_description&) override;

        void plugin_initialize(const variables_map&);
        void plugin_startup();
        void plugin_shutdown();
   };

}
