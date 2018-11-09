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

  /**
   * This structure holds all informations needed during distribution period.
  */
  struct init_data
  {
    /**
     * An owner of given data.
     */
    account_name  owner;

    uint64_t primary_key()const { return owner; }

    EOSLIB_SERIALIZE( init_data, (owner) )

  };

  typedef eosio::multi_index<N(initproxy), init_data> inits;

  class gateway : public contract {
    public:

      gateway( account_name self )
                : contract( self )
      {
      }

      /**
      * Triggered by `transfer` action. The `transfer` action is executed
      * when user from bitshares blockchain wants to exchange BTS to staked BEOS.
      * The `transfer` method exists in BEOS plugin( method `transfer` in `beos_plugin.cpp` )
      * 
      * `to`        - given account
      * `quantity`  - number of BEOS-es. Ratio is `1` - when an user sends 125 BTS, then 125 staked BEOS-es are saved
      */
      void issue(account_name to, asset quantity );

      /**
      * Executed by any user at any time. If the user wants to decrease balance
      * then can call this action via wallet. After this action, next rewards will be smaller,
      * because balance of the user is smaller.
      * At the end of distribution period the user gets RAM and BEOSes,
      * if before this action the user gathered any.
      * 
      * `owner`     - owner of account
      * `quantity`  - amount which will be withdrawn
      */
      void withdraw( account_name owner, asset quantity );

      void add( account_name owner, account_name ram_payer );
    private:

      void checker( account_name any_account, asset value );
  };

} /// namespace eosio
