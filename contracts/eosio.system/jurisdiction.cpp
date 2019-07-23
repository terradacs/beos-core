/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */

#include "eosio.system.hpp"

#include <eosio.token/eosio.token.hpp>

namespace eosiosystem {

   void system_contract::addjurisdict( account_name ram_payer, code_jurisdiction new_code, std::string new_name, std::string new_description )
   {
      eosio::print("Entering system_contract::addjurisdict\n");
      __addsinglejurisdiction<true>(ram_payer, new_code, new_name, new_description);
      eosio::print("Leaving eosio only system_contractaddjurisdict\n");
   }

   void system_contract::addmultijurs(std::vector<new_jurisdic_info> new_jurisdicts)
   {
      eosio::print("Entering system_contract eosio only::addmultijurs\n");
      require_auth( _self );

      //Vector should be shorter than the limit
      eosio_assert( new_jurisdicts.size() < limit_256, std::string("amount of records is higher than allowed: " + std::to_string(limit_256)).c_str());

      for(const auto& var : new_jurisdicts) __addsinglejurisdiction<false>(_self, var.new_code, var.new_name, var.new_description);
      
      eosio::print("Leaving eosio only system_contract::addmultijurs\n");
   }

   void system_contract::updateprod( eosio::jurisdiction_producer data )
   {
      eosio::print( ( "Entering system_contract::updateprod for producer: " + name{ data.producer }.to_string() + "\n" ).c_str() );
      require_auth( data.producer );

      eosio_assert( data.jurisdictions.size() < limit_256, "number of jurisdictions is greater than allowed" );

      typedef eosio::multi_index< N(producers), eosiosystem::producer_info > producer_info_t;
      producer_info_t _producers( N(eosio), N(eosio) );

      auto _found_producer = _producers.find( data.producer );
      eosio_assert( _found_producer != _producers.end(), "user is not a producer" );

      size_t size = action_data_size();
      std::unique_ptr<char, decltype(&free)> buffer( reinterpret_cast<char*>( malloc( size ) ), &free );
      read_action_data( buffer.get(), size );
      update_jurisdictions( buffer.get(), size );

      eosio::print("Leaving system_contract::updateprod\n");
   }

   void system_contract::updatejurfee(asset quantity)
   {
      eosio::print("Entering system_contract eosio only - updatejurfee");

      require_auth( _self );
      eosio_assert( quantity.symbol == asset().symbol , std::string("only native coin allowed").c_str() );

      _jurisdiction_gstate.jurisdiction_fee = quantity;
      _jurisdiction_global.set(_jurisdiction_gstate, _self);

      eosio::print("Leaving system_contract::updatejurfee");
   }

   void system_contract::updatejuracc(account_name target_account)
   {
      eosio::print("Entering system_contract eosio only - updatejuracc");

      require_auth( _self );
      eosio_assert( is_account( target_account ), "target account must exist");

      _jurisdiction_gstate.jurisdiction_fee_receiver = target_account;
      _jurisdiction_global.set(_jurisdiction_gstate, _self);

      eosio::print("Leaving system_contract::updatejuracc");
   }

   template<bool fee_enabled>
   void system_contract::__addsinglejurisdiction(const account_name ram_payer, const code_jurisdiction new_code, const std::string new_name, const std::string new_description )
   {      
      require_auth( ram_payer );

      eosio_assert( new_name.size() < limit_256, "size of name is greater than allowed" );
      eosio_assert( new_description.size() < limit_256, "size of description is greater than allowed" );

      add_jurisdiction( ram_payer, new_code, const_cast<char*>(new_name.c_str()), new_name.size(), const_cast<char*>(new_description.c_str()), new_description.size());

      if(fee_enabled && ram_payer != _self)
      {
         //Preventing against spamming
         INLINE_ACTION_SENDER(eosio::token, transfer)( N(eosio.token), {ram_payer,N(active)},
                                                         { ram_payer, _jurisdiction_gstate.jurisdiction_fee_receiver, _jurisdiction_gstate.jurisdiction_fee, "jurisdiction fee" } );
      }      
   }

} //namespace eosiosystem