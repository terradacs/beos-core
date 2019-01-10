#pragma once

#include <eosio/chain/abi_def.hpp>
#include <eosio/chain/contract_table_objects.hpp>
#include <eosio/chain/abi_serializer.hpp>

#include <chainbase/chainbase.hpp>

#include <fc/variant_object.hpp>

namespace eosio {
namespace chain {

class controller;
struct controller_impl;

struct table_helper
{
   static const std::string KEYi64;
   static abi_def get_abi( const controller& db, const name& account );
   static std::string get_table_type( const abi_def& abi, const name& table_name );
   static float64_t to_softfloat64( double d );
   static void copy_inline_row(const chain::key_value_object& obj, vector<char>& data);
   static fc::variant get_global_row( const chainbase::database& db, const abi_def& abi, const abi_serializer& abis, const fc::microseconds& abi_serializer_max_time_ms, bool shorten_abi_errors );
};

} }
