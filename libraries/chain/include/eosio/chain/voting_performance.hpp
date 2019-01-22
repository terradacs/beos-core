#pragma once

#include <eosio/chain/types.hpp>
#include <eosio/chain/table_helper.hpp>

#include <chainbase/chainbase.hpp>

#include "multi_index_includes.hpp"

#include <eosiolib/block_producer_voting_info.hpp>

#include <fc/variant_object.hpp>

#include <functional>
#include <vector>

namespace eosio {
namespace chain {

class controller;

namespace aux
{
   inline void eosio_assert(bool condition, const char* msg)
   {
   if(BOOST_UNLIKELY(!condition)) {
      std::string message(msg);
      edump((message));
      EOS_THROW(eosio_assert_message_exception, "assertion failure with message: ${s}", ("s", message));
      }
   }
}

class producer_information
{
   private:

      using p_block_producer_voting_info = std::shared_ptr< block_producer_voting_info >;

   public:

      using producer_info_index = boost::container::flat_map< account_name, p_block_producer_voting_info >;

   private:

      const controller& _controller;
      const chainbase::database& _db;

      const table_id_object* table_id = nullptr;
      abi_def abi;
      abi_serializer abis;

      producer_info_index gathered_producers;

      void refresh();

      void get_actual_producer( const account_name& acnt, producer_info_index::iterator& found );
      void add_producer( const fc::variant& v );

      std::vector<fc::variant> get_producers( const fc::microseconds& abi_serializer_max_time );

   public:

      producer_information( const controller& c, const chainbase::database& d );

      void clear();

      template< typename CALLABLE >
      void process_producer( const account_name& acnt, CALLABLE call )
      {
         producer_info_index::iterator found;

         get_actual_producer( acnt, found );
         call( found, found != gathered_producers.end() );
      }

      std::vector<fc::variant> get_producers( const fc::microseconds& abi_serializer_max_time, bool shorten_abi_errors, bool json, const std::string& lower_bound, uint32_t limit, double& total_producer_vote_weight, std::string& more );
};

class wasm_data_writer
{
   public:

      using res_pair = std::pair< block_producer_voting_info*, bool >;

   private:

      using t_memory = boost::container::flat_map< account_name, uint32_t >;

      uint32_t idx = 0;
      uint32_t max = 0;
      t_memory memory;

      block_producer_voting_info* ptr = nullptr;

      res_pair get( const account_name& owner );

   public:

      uint32_t get_size() const { return idx; };

      void clear( block_producer_voting_info* _ptr, uint32_t _max );
      void save( const account_name& owner, double total_votes, bool is_active );
};

} }
