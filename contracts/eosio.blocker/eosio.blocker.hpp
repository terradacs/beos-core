/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */
#pragma once

#include <eosiolib/asset.hpp>
#include <eosiolib/eosio.hpp>

#include <string>

namespace eosio {

  class blocker : public contract {
    private:

      struct account_data {
         account_name account;
         uint64_t primary_key()const { return account; }
      };

      typedef eosio::multi_index< N(validsenders),  account_data > valid_senders_type;
      typedef eosio::multi_index< N(validrecip),    account_data > valid_recip_type;

      void add_account( account_name account, bool from );
      void remove_account( account_name account, bool from );

    public:

      blocker( account_name self ) : contract( self ){}

      void update( account_name account, bool from, bool insert );

      bool is_valid() const;
  };

} /// namespace eosio
