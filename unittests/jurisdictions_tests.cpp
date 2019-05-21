#include <boost/test/unit_test.hpp>
#include <eosio/testing/tester.hpp>
#include <eosio/chain/abi_serializer.hpp>
#include <eosio/chain/resource_limits.hpp>
#include <Runtime/Runtime.h>

#include <eosio/chain/jurisdiction_object.hpp>
#include <eosio/chain/jurisdiction_objects.hpp>

using namespace eosio::testing;
using namespace eosio;
using namespace eosio::chain;
using namespace eosio::testing;
using namespace fc;

using eosio::chain::trx_jurisdiction;
using eosio::chain::jurisdiction_helper;

class jurisdiction_tester : public tester
{
   public:

      jurisdiction_tester()
      {
      }

      bool check_jurisdictions( const chainbase::database &db, const jurisdiction_updater_ordered& src )
      {
         const auto& idx = db.get_index< jurisdiction_index, by_producer_jurisdiction >();
         auto itr = idx.lower_bound( std::make_tuple( src.producer, std::numeric_limits< code_jurisdiction >::min() ) );

         auto jurisdictions = src.jurisdictions;

         if( itr == idx.end() )
            return jurisdictions.empty();

         bool res = true;

         auto itr_src = jurisdictions.begin();

         while( itr != idx.end() && itr->producer == src.producer )
         {
            if( itr->jurisdiction != *itr_src )
               return false;

            ++itr;
            ++itr_src;
         }

         BOOST_REQUIRE_EQUAL( true, itr == idx.end() || itr->producer != src.producer );
         BOOST_REQUIRE_EQUAL( true, itr_src == jurisdictions.end() );

         return res;
      }
};

BOOST_AUTO_TEST_SUITE(jurisdiction_tests)

BOOST_FIXTURE_TEST_CASE( basic_test, jurisdiction_tester ) try {

   using data_type = std::vector< code_jurisdiction >;

   trx_jurisdiction src;

   const uint16_t idx = 0;
   data_type src_data = { 6, 3, 44, 55, 1, 2, 8, 4, 2 };

   //Serializing
   src.jurisdictions = src_data;
   std::vector< char > bytes_stream = fc::raw::pack( src );

   //Saving data
   extensions_type any_extension;
   any_extension.push_back( std::make_pair( idx, bytes_stream ) );

   //Deserializing
   jurisdiction_helper reader;

   auto deserialized_data = reader.read( any_extension );
   BOOST_REQUIRE_EQUAL( 1, deserialized_data.size() );

   data_type dst = deserialized_data[0].jurisdictions;

   BOOST_REQUIRE_EQUAL( dst.size(), src_data.size() );
   BOOST_REQUIRE_EQUAL( true, std::equal( dst.begin(), dst.end(), src_data.begin() ) );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_test_01, jurisdiction_tester ) try {

   using data_type = std::vector< code_jurisdiction >;
   using buffer = std::vector< char >;

   trx_jurisdiction src;

   const uint16_t idx = 0;
   std::vector< data_type > v_data_type = { { 5,6,7,8,9 }, { 0,1 }, { 2 }, { 3,4,5 } };
   std::vector< buffer > buffers;

   //Serializing
   for( const auto& item : v_data_type )
   {
      src.jurisdictions = item;
      buffers.emplace_back( fc::raw::pack( src ) );
   }

   //Saving data
   extensions_type any_extension;
   for( const auto& item : buffers )
      any_extension.emplace_back( std::make_pair( idx, item ) );

   //Deserializing
   jurisdiction_helper reader;

   auto deserialized_data = reader.read( any_extension );
   BOOST_REQUIRE_EQUAL( v_data_type.size(), deserialized_data.size() );

   uint32_t i = 0;
   for( auto& item : v_data_type )
   {
      data_type dst = deserialized_data[ i++ ].jurisdictions;
      BOOST_REQUIRE_EQUAL( dst.size(), item.size() );
      BOOST_REQUIRE_EQUAL( true, std::equal( dst.begin(), dst.end(), item.begin() ) );
   }
} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_test_02, jurisdiction_tester ) try {

   chainbase::database &db = const_cast< chainbase::database& > ( control->db() );
   jurisdiction_helper updater;

   jurisdiction_updater_ordered src;
   src.producer = N(tester);

   src.jurisdictions = {};
   updater.update( db, src );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src ) );

   src.jurisdictions = { 6,5,1,2,3,4,5 };
   updater.update( db, src );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src ) );

   src.jurisdictions = { 2 };
   updater.update( db, src );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src ) );

   src.jurisdictions = { 7,8,9,10,11,12 };
   updater.update( db, src );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src ) );

   src.jurisdictions = { 7,10,11,13 };
   updater.update( db, src );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src ) );

   src.jurisdictions = { 13,14 };
   updater.update( db, src );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src ) );

   src.jurisdictions = { 10,11,12,13,14 };
   updater.update( db, src );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src ) );

   src.jurisdictions = { 14,15,16,20 };
   updater.update( db, src );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src ) );

   src.jurisdictions = { 14,16,20,21 };
   updater.update( db, src );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src ) );

   src.jurisdictions = {};
   updater.update( db, src );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src ) );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_test_03, jurisdiction_tester ) try {

   chainbase::database &db = const_cast< chainbase::database& > ( control->db() );
   jurisdiction_helper updater;

   jurisdiction_updater_ordered src_01;
   src_01.producer = N(tester_01);
   src_01.jurisdictions = { 0,1,2,3,4 };

   jurisdiction_updater_ordered src_02;
   src_02.producer = N(tester_02);

   src_01.jurisdictions = { 0,1,2,3,4 };
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { 5,6,7,8,9 };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );

   src_01.jurisdictions = { 3,4,5,6,7 };
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { 5,6,7,8,9 };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );

   src_01.jurisdictions = { 3,4,5,6,7 };
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );

   src_01.jurisdictions = {};
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { 3,4,5,6,7 };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );

   src_01.jurisdictions = { 3,4,5 };
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { 3,4,5,6,7,8 };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );

   src_01.jurisdictions = { 9 };
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { 7,8 };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );

   src_01.jurisdictions = { 7,8,9 };
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { 7 };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );

   src_01.jurisdictions = { 7 };
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { 7,8 };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );

   src_01.jurisdictions = { 0,1 };
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { 0,1,2,3 };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );

   src_01.jurisdictions = { 0 };
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { 0 };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );

   src_01.jurisdictions = { 0,1,2,3 };
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { 1,3,4 };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, check_jurisdictions( db, src_02 ) );

} FC_LOG_AND_RETHROW()

BOOST_AUTO_TEST_SUITE_END()
