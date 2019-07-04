#pragma once
#include <eosiolib/eosio.hpp>
#include <eosiolib/privileged.hpp>

namespace eosio {

   class bios : public contract {
      public:
         bios( action_name self ):contract(self){}

         void setpriv( account_name account, uint8_t ispriv ) {
            require_auth( _self );
            set_privileged( account, ispriv );
         }

         void setalimits( account_name account, int64_t ram_bytes, int64_t net_weight, int64_t cpu_weight ) {
            require_auth( _self );
            set_resource_limits( account, ram_bytes, net_weight, cpu_weight );
         }

         void setglimits( uint64_t ram, uint64_t net, uint64_t cpu ) {
            (void)ram; (void)net; (void)cpu;
            require_auth( _self );
         }

         void setprods( std::vector<eosio::producer_key> schedule ) {
            (void)schedule; // schedule argument just forces the deserialization of the action data into vector<producer_key> (necessary check)
            require_auth( _self );

            size_t size = action_data_size();
            std::unique_ptr<char, decltype(&free)> buffer( reinterpret_cast<char*>( malloc( size ) ), &free );
            read_action_data( buffer.get(), size );
            set_proposed_producers(buffer.get(), size);
         }

         void setparams( const eosio::blockchain_parameters& params ) {
            require_auth( _self );
            set_blockchain_parameters( params );
         }

         void reqauth( action_name from ) {
            require_auth( from );
         }

      private:
   };

} /// namespace eosio
