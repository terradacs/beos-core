/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */
#include <eosio/beos_api_plugin/beos_api_plugin.hpp>
#include <eosio/chain/exceptions.hpp>

#include <fc/io/json.hpp>

namespace eosio {

static appbase::abstract_plugin& _beos_api_plugin = app().register_plugin<beos_api_plugin>();

beos_api_plugin::beos_api_plugin(){}
beos_api_plugin::~beos_api_plugin(){}

void beos_api_plugin::set_program_options(options_description&, options_description&) {}
void beos_api_plugin::plugin_initialize(const variables_map&) {}

#define CALL(api_name, api_handle, api_namespace, call_name, http_response_code) \
{std::string("/v1/" #api_name "/" #call_name), \
   [this, api_handle](string, string body, url_response_callback cb) mutable { \
          try { \
             if (body.empty()) body = "{}"; \
             auto result = api_handle.call_name(fc::json::from_string(body).as<api_namespace::call_name ## _params>()); \
             cb(http_response_code, fc::json::to_string(result)); \
          } catch (...) { \
             http_plugin::handle_exception(#api_name, #call_name, body, cb); \
          } \
       }}

#define CHAIN_RW_CALL(call_name, http_response_code) CALL(beos, rw_api, beos_apis::read_write, call_name, http_response_code)

void beos_api_plugin::plugin_startup() {
   ilog( "starting beos_api_plugin" );

   auto rw_api = app().get_plugin<beos_plugin>().get_read_write_api();

   app().get_plugin<http_plugin>().add_api({
      CHAIN_RW_CALL(transfer, 200l),
      CHAIN_RW_CALL(address_validator, 200l)
   });
}

void beos_api_plugin::plugin_shutdown() {}

}
