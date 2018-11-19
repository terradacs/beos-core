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

  class gateway : public contract {
    public:

      gateway( account_name self )
                : contract( self )
      {
      }

      /**
      * Triggered by user. This action is executed
      * when user from bitshares blockchain wants to exchange BTS to PXBTS.
      * 
      * `to`        - given account
      * `quantity`  - number of PXBTS-es.
      */
      void issue(account_name to, asset quantity );

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
