#include <boost/test/unit_test.hpp>
#include <eosio/testing/tester.hpp>
#include <eosio/chain/abi_serializer.hpp>
#include <eosio/chain/resource_limits.hpp>
#include <Runtime/Runtime.h>

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
   BOOST_REQUIRE_EQUAL( true, reader.read( any_extension ) );
   auto deserialized_data = reader.get_jurisdictions();

   BOOST_REQUIRE_EQUAL( 1, deserialized_data.size() );

   data_type dst = deserialized_data[0].jurisdictions;

   BOOST_REQUIRE_EQUAL( dst.size(), src_data.size() );
   BOOST_REQUIRE_EQUAL( true, std::equal( dst.begin(), dst.end(), src_data.begin() ) );

} FC_LOG_AND_RETHROW()

BOOST_AUTO_TEST_SUITE_END()
