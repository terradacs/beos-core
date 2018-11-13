/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */
#pragma once
#include <appbase/application.hpp>
#include <eosio/chain/controller.hpp>
#include <eosio/chain_plugin/chain_plugin.hpp>

namespace eosio {

  using std::unique_ptr;
  using chain::controller;

  using namespace appbase;

namespace beos_apis
{

  class read_write
  {
    public:

      /**
       * This structure holds account name to verify.
       */

      struct address_validator_params
      {
        std::string account_name;
      };

     /**
      * RPC request example:

        curl --url http://127.0.0.1:8888/v1/beos/address_validator --data
         '{
            "account_name":"eosio"
          }
          '
     */

      /**
       * This structure holds information if given account exists.
       */

      struct address_validator_results 
      {
        bool is_valid;
        address_validator_results(bool _valid ) : is_valid(_valid)
        {
        }
      };


    private:

      controller& db;
      const fc::microseconds abi_serializer_max_time;

    public:

      read_write( controller& db, const fc::microseconds& abi_serializer_max_time )
          : db( db ), abi_serializer_max_time( abi_serializer_max_time ) {}


      address_validator_results address_validator( const address_validator_params& _account_name );
  };

} // namespace chain_apis

class beos_plugin : public plugin<beos_plugin>
{
   public:

      APPBASE_PLUGIN_REQUIRES((beos_plugin))

      beos_plugin();
      virtual ~beos_plugin();

      virtual void set_program_options(options_description& cli, options_description& cfg) override;

      void plugin_initialize(const variables_map& options);
      void plugin_startup();
      void plugin_shutdown();

      beos_apis::read_write get_read_write_api() const;

   private:

    unique_ptr<class beos_plugin_impl> my;
};

} /// namespace eosio

FC_REFLECT( eosio::beos_apis::read_write::address_validator_params, (account_name))
FC_REFLECT( eosio::beos_apis::read_write::address_validator_results, (is_valid) )