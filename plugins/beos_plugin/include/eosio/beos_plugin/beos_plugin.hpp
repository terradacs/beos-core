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

  #define OK_STATUS "OK"
  #define FAIL_STATUS "FAILED"

  class read_write
  {
    public:

      /**
       * This structure holds all informations needed for:
       *    a) account creation + holding balance ( `eosio.interchain.lock` action )
       *    b) holding balance ( `eosio.interchain.lock` action )
       * 
       * It depends on `create_account`.
       * `create_account` == `1` variant `a`
       * `create_account` == `0` variant `b`
      */
      struct transfer_params
      {
        std::string creator;
        std::string account;
        std::string owner_key;
        std::string active_key;
        std::string ram;

        std::string account_contract;
        std::string action;

        std::string from;
        std::string quantity;

        bool create_account;
      };

     /**
      * RPC request example:

        curl --url http://127.0.0.1:8888/v1/beos/transfer --data
          '{
            "creator": "eosio",
            "account": "dude2",
            "owner_key": "EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV",
            "active_key": "EOS6AAWx6uvqu5LMBt8vCNYXcxjrGmd3WvffxkBM4Uozs4e1dgBF3",
            "ram": "0.0006 SYS",
            "account_contract": "beos.token",
            "action": "lock",
            "from": "beos.token",
            "quantity": "200.0000 SYS",
            "create_account": 1
          }
          '
     */

      /**
       * Helper structure used to response on RPC request.
      */
      struct transfer_results
      {
        string status;

        transfer_results( bool val = true ): status( val ? OK_STATUS : FAIL_STATUS )
        {
        }
      };


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

      std::string beos_token_key;
      std::string eosio_key;

      void create_any_action( chain::action& act, account_name account_contract, const std::string& action, fc::variant& act_data, vector< chain::permission_level >&& permissions );

      void create_newaccount_action( chain::action& act, const transfer_params& params, chain::public_key_type&& owner_key );
      void create_buy_action( chain::action& act, const transfer_params& params );
      void create_lock_action( chain::action& act, const transfer_params& params );
    
      transfer_results push_transaction( std::vector< chain::action >&& actions, std::vector< chain::private_key_type >&& keys );

    public:

      read_write( controller& db, const fc::microseconds& abi_serializer_max_time, std::string beos_token_key = "", std::string eosio_key = "" )
          : db( db ), abi_serializer_max_time( abi_serializer_max_time ), beos_token_key( beos_token_key ), eosio_key( eosio_key ) {}

      transfer_results transfer( const transfer_params& );
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

FC_REFLECT( eosio::beos_apis::read_write::transfer_params, (creator)(account)(owner_key)(active_key)(ram)(account_contract)(action)(from)(quantity)(create_account) )
FC_REFLECT( eosio::beos_apis::read_write::transfer_results, (status) )
FC_REFLECT( eosio::beos_apis::read_write::address_validator_params, (account_name))
FC_REFLECT( eosio::beos_apis::read_write::address_validator_results, (is_valid) )