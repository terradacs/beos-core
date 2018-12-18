/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */
#pragma once

#include <eosiolib/asset.hpp>
#include <eosiolib/eosio.hpp>
#include <eosiolib/singleton.hpp>

#include <string>

namespace eosio {

  using std::string;

   struct gateway_proxy_asset
   {
      asset proxy_asset;
      std::string description;

      EOSLIB_SERIALIZE( gateway_proxy_asset, (proxy_asset)(description) )
   };
   struct gateway_global_state
   {
      std::vector< gateway_proxy_asset > proxy_assets;

      EOSLIB_SERIALIZE( gateway_global_state, (proxy_assets) )
   };

   typedef eosio::singleton<N(gatewaystate), gateway_global_state> gateway_global_state_singleton;

  class gateway : public contract {
    private:

      gateway_global_state            _gstate;
      gateway_global_state_singleton  _global;

      gateway_global_state get_default_parameters()
      {
         return gateway_global_state();
      }

      std::string get_description( const asset& proxy_asset );

    public:

      gateway( account_name self )
                : contract( self ),
                  _global( _self, _self )
      {
         _gstate = _global.exists() ? _global.get() : get_default_parameters();
      }

      void changeparams( gateway_global_state new_params );

      /**
      * Triggered by user. This action is executed
      * when user from bitshares blockchain wants to exchange BTS to PXBTS.
      * 
      * `to`        - given account
      * `quantity`  - number of PXBTS-es.
      */
      void issue(account_name to, asset quantity, std::string memo = "");

      /**
      * Executed by any user at any time. If the user wants to decrease balance
      * then can call this action via wallet. After this action, next rewards will be smaller,
      * because balance of the user is smaller.
      * At the end of distribution period the user gets RAM and BEOSes,
      * if before this action the user gathered any.
      * 
      * `from`     - owner of account
      * `bts_to`     - owner of account in 'bitshares' blockchain
      * `quantity`  - amount which will be withdrawn
      */
      void withdraw( account_name from, std::string bts_to, asset quantity );
    private:

      void checker( account_name any_account, asset value );
  };

} /// namespace eosio
