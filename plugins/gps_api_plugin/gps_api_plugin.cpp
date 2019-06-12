/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */
#include <eosio/gps_api_plugin/gps_api_plugin.hpp>
#include <eosio/chain/exceptions.hpp>

#include <fc/io/json.hpp>

namespace eosio {

static appbase::abstract_plugin& _gps_api_plugin = app().register_plugin<gps_api_plugin>();

gps_api_plugin::gps_api_plugin(){}
gps_api_plugin::~gps_api_plugin(){}

void gps_api_plugin::set_program_options(options_description&, options_description&) {}
void gps_api_plugin::plugin_initialize(const variables_map& options) {
   try {
      const auto& _http_plugin = app().get_plugin<http_plugin>();
      if( !_http_plugin.is_on_loopback()) {
         wlog( "\n"
               "**********SECURITY WARNING**********\n"
               "*                                  *\n"
               "* --        GPS API             -- *\n"
               "* - EXPOSED to the LOCAL NETWORK - *\n"
               "* - USE ONLY ON SECURE NETWORKS! - *\n"
               "*                                  *\n"
               "************************************\n" );

      }
   } FC_LOG_AND_RETHROW()
}

#define CALL(api_name, api_handle, api_namespace, call_name, http_response_code) \
{std::string("/v1/" #api_name "/" #call_name), \
   [api_handle](string, string body, url_response_callback cb) mutable { \
          try { \
             if (body.empty()) body = "{}"; \
             auto result = api_handle.call_name(fc::json::from_string(body).as<api_namespace::call_name ## _params>()); \
             cb(http_response_code, fc::json::to_string(result)); \
          } catch (...) { \
             http_plugin::handle_exception(#api_name, #call_name, body, cb); \
          } \
       }}

#define CHAIN_RW_CALL(call_name, http_response_code) CALL(gps, rw_api, gps_apis::read_write, call_name, http_response_code)

void gps_api_plugin::plugin_startup() {
   ilog( "starting gps_api_plugin" );

   auto rw_api = app().get_plugin<gps_plugin>().get_read_write_api();

   app().get_plugin<http_plugin>().add_api({
      CHAIN_RW_CALL(update_jurisdictions, 200l)
   });
}

void gps_api_plugin::plugin_shutdown() {}

}
