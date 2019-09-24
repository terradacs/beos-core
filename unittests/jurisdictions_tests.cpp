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

using eosio::chain::jurisdiction_basic;
using eosio::chain::jurisdiction_manager;
using eosio::chain::transaction_validator;

class jurisdiction_tester : public tester
{
   protected:

      using data_type = std::vector< code_jurisdiction >;

      transaction_validator validator;

   public:

      jurisdiction_tester()
      {
      }

      void make_jurisdictions( chainbase::database &db, int8_t max )
      {
         jurisdiction_manager updater;

         jurisdiction_dictionary dict;
         dict.description = "DESC";

         for( int8_t i = 0; i < max; ++i )
         {
            dict.code = i;
            dict.name = std::to_string( i );
            updater.update( db, dict );
         }

      }

      action create_updateprod_action( const data_type& updateprod_codes )
      {
         action act;
         act.account = config::system_account_name;
         act.name = N(updateprod);
         act.authorization = vector<permission_level>{{config::system_account_name, config::active_name}};
         act.data = fc::raw::pack( jurisdiction_producer { account_name(), updateprod_codes } );

         return act;
      }

      transaction create_transaction( bool allow_trx_codes, const data_type& trx_codes, bool allow_updateprod, const data_type& updateprod_codes )
      {
         const uint16_t idx = 0;

         transaction trx;

         if( allow_trx_codes )
         {
            jurisdiction_basic src;
            src.jurisdictions = trx_codes;
            trx.transaction_extensions.push_back( { idx, fc::raw::pack( src ) } );
         }

         if( allow_updateprod )
            trx.actions.emplace_back( create_updateprod_action( updateprod_codes ) );

         return trx;
      }

      bool validate_trx( bool allow_trx_codes, const data_type& trx_codes, bool allow_updateprod, const data_type& updateprod_codes, account_name producer = account_name() )
      {
         auto validation_result = validator.validate_transaction( create_transaction( allow_trx_codes, trx_codes, allow_updateprod, updateprod_codes ), producer );
         return validation_result.first;
      }

      bool is_any_updateprod_action_in_transaction( bool allow_updateprod, account_name producer )
      {
         auto validation_result = validator.validate_transaction( create_transaction( false/*allow_trx_codes*/, {}/*trx_codes*/, allow_updateprod, {}/*updateprod_codes*/ ), producer );
         return validation_result.second;
      }

      void clear()
      {
         validator.clear();
      }

};

BOOST_AUTO_TEST_SUITE(jurisdiction_tests)

/*
   There are examples how incoming transaction are put inside block.
   When a transaction has `updateprod` action and new jurisdictions don't match to jurisdictions in previous transactions,
   then the transaction with `updateprod` is removed from block and moved to next block.

   For every block is assumption, that given producer has all possible jurisdictions at the start,
   otherwise is impossible to execute `transaction_validator::validate_transaction`( here `validate_trx` ),
   because this call is blocked by `jurisdiction_mgr.transaction_jurisdictions_match` in producer plugin.

   Every section is treated as next block.
*/
BOOST_FIXTURE_TEST_CASE( mix_test, jurisdiction_tester ) try {
   {
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
   }
   {
      clear();
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
   }
   {
      clear();
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {1}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {2}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {3}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {1,5,2,3}/*updateprod_codes*/ ) );
   }
   {
      clear();
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {1}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {2}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {3}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {5,2,3}/*updateprod_codes*/ ) );
   }
   {
      clear();
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {1}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {2}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {3}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
   }
   {
      clear();
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {1}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {1,2}/*updateprod_codes*/ ) );
   }
   {
      clear();
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {2}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {1}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {3,2,1}/*updateprod_codes*/ ) );
   }
   {
      clear();
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {2}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {1}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {4,5}/*updateprod_codes*/ ) );
   }
   {
      clear();
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {2}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {1}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {1,2,3}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {3}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {3}/*updateprod_codes*/ ) );
   }
   {
      clear();
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {2}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {1,2,3}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {3}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {1}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {3,2,4,5,1}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {1,3,4}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {3,4,5,1}/*updateprod_codes*/ ) );
   }
   {
      clear();
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {1,2,3}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {1,2,3,4}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {3}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {5}/*updateprod_codes*/ ) );
   }
   {
      clear();
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {2}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {1,2,3}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {3}/*trx_codes*/, true/*allow_updateprod*/, {1,2,3,4}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {3}/*trx_codes*/, true/*allow_updateprod*/, {1,2,3}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {1,2}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {2}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {1}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {2,3}/*updateprod_codes*/ ) );
   }
   {
      clear();
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {0}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {1}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {3,2,1,0}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {3}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {1,2,3,4,5,6}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {6,5,4,3,2,1,0}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {6,1,3,0}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {1,3,0}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {1,3}/*updateprod_codes*/ ) );
   }
   {
      clear();
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {0}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {1}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {0}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
   }
   {
      clear();
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {0,1,2}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {0}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {1}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {2}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {0,1}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {3}/*updateprod_codes*/ ) );
   }
   {
      clear();
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {1}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {2,3}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {4}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {4,1}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {2,3}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {1,2,3,4}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {4}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {1,2,3}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {4,2,3}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {1,4}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {1,2,4,5}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {5}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {1,2,3,4}/*updateprod_codes*/ ) );
   }
   {
      clear();
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {0}/*trx_codes*/, true/*allow_updateprod*/, {1}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {1}/*trx_codes*/, true/*allow_updateprod*/, {2,0}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {2}/*trx_codes*/, true/*allow_updateprod*/, {3,1,0}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {3}/*trx_codes*/, true/*allow_updateprod*/, {4,2,1,0}/*updateprod_codes*/ ) );
   }
   {
      clear();
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {0}/*trx_codes*/, true/*allow_updateprod*/, {1,2,3}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {2,3}/*trx_codes*/, true/*allow_updateprod*/, {1,2,3,4,0}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {0,1}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {2,3}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  true/*allow_trx_codes*/, {1,2,3}/*trx_codes*/, true/*allow_updateprod*/, {7,8}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {4}/*trx_codes*/, true/*allow_updateprod*/, {7,8,2,0}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {7}/*trx_codes*/, false/*allow_updateprod*/, {4,0,3}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {8}/*trx_codes*/, false/*allow_updateprod*/, {0,2,3,4,7}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  true/*allow_trx_codes*/, {0,2,3,4,7,1,8}/*trx_codes*/, true/*allow_updateprod*/, {0,2,3,4,7,1}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( true, validate_trx(  true/*allow_trx_codes*/, {0,2,3,4,7,1,8}/*trx_codes*/, true/*allow_updateprod*/, {0,2,3,4,8,7,1}/*updateprod_codes*/ ) );
   }
   {
      clear();
      BOOST_REQUIRE_EQUAL( true, validate_trx(  false/*allow_trx_codes*/, {}/*trx_codes*/, true/*allow_updateprod*/, {1}/*updateprod_codes*/ ) );
      BOOST_REQUIRE_EQUAL( false, validate_trx(  true/*allow_trx_codes*/, {0}/*trx_codes*/, false/*allow_updateprod*/, {}/*updateprod_codes*/ ) );
   }

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( find_updateprod_test, jurisdiction_tester ) try {
/*
   There are 3 options:

   - exists `system_contract::updateprod` action AND producer in `system_contract::updateprod` is the same as actual producer that produces block
      -> required answer `true`

   - exists `system_contract::updateprod` action AND producer in `system_contract::updateprod` is different from as actual producer that produces block
      -> required answer `true`

   - doesn't exist `system_contract::updateprod` action
      -> required answer `false`

   Note!
      By default and for simplification producer in `system_contract::updateprod` is always empty i.e. `account_name()`
*/
   {
      BOOST_REQUIRE_EQUAL( true, is_any_updateprod_action_in_transaction( true/*allow_updateprod*/, account_name() ) );
      BOOST_REQUIRE_EQUAL( true, is_any_updateprod_action_in_transaction( true/*allow_updateprod*/, N(other) ) );

      BOOST_REQUIRE_EQUAL( false, is_any_updateprod_action_in_transaction( false/*allow_updateprod*/, account_name() ) );
      BOOST_REQUIRE_EQUAL( false, is_any_updateprod_action_in_transaction( false/*allow_updateprod*/, N(other) ) );
   }

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_test, jurisdiction_tester ) try {

   jurisdiction_basic src;

   const uint16_t idx = 0;
   data_type src_data = { 6, 3, 44, 55, 1, 2, 8, 4, 2 };

   //Serializing
   src.jurisdictions = src_data;
   std::vector< char > bytes_stream = fc::raw::pack( src );

   //Saving data
   extensions_type any_extension;
   any_extension.push_back( extension_storage{ idx, bytes_stream } );

   //Deserializing
   jurisdiction_manager reader;

   auto deserialized_data = reader.read( any_extension );
   BOOST_REQUIRE_EQUAL( 1, deserialized_data.size() );

   data_type dst = deserialized_data[0].jurisdictions;

   BOOST_REQUIRE_EQUAL( dst.size(), src_data.size() );
   BOOST_REQUIRE_EQUAL( true, std::equal( dst.begin(), dst.end(), src_data.begin() ) );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_test_01, jurisdiction_tester ) try {

   using buffer = std::vector< char >;

   jurisdiction_basic src;

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
      any_extension.emplace_back( extension_storage{ idx, item } );

   //Deserializing
   jurisdiction_manager reader;

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
   jurisdiction_manager updater;

   jurisdiction_producer_ordered src( N(tester) );

   make_jurisdictions( db, 22 );

   src.jurisdictions = {};
   updater.update( db, src );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src ) );

   src.jurisdictions = { 6,5,1,2,3,4,5 };
   updater.update( db, src );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src ) );

   src.jurisdictions = { 2 };
   updater.update( db, src );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src ) );

   src.jurisdictions = { 7,8,9,10,11,12 };
   updater.update( db, src );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src ) );

   src.jurisdictions = { 7,10,11,13 };
   updater.update( db, src );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src ) );

   src.jurisdictions = { 13,14 };
   updater.update( db, src );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src ) );

   src.jurisdictions = { 10,11,12,13,14 };
   updater.update( db, src );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src ) );

   src.jurisdictions = { 14,15,16,20 };
   updater.update( db, src );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src ) );

   src.jurisdictions = { 14,16,20,21 };
   updater.update( db, src );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src ) );

   src.jurisdictions = {};
   updater.update( db, src );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src ) );

} FC_LOG_AND_RETHROW()

BOOST_FIXTURE_TEST_CASE( basic_test_03, jurisdiction_tester ) try {

   chainbase::database &db = const_cast< chainbase::database& > ( control->db() );
   jurisdiction_manager updater;

   make_jurisdictions( db, 10 );

   jurisdiction_producer_ordered src_01( N(tester_01), { 0,1,2,3,4 } );

   jurisdiction_producer_ordered src_02( N(tester_02) );

   src_01.jurisdictions = { 0,1,2,3,4 };
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { 5,6,7,8,9 };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );

   src_01.jurisdictions = { 3,4,5,6,7 };
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { 5,6,7,8,9 };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );

   src_01.jurisdictions = { 3,4,5,6,7 };
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );

   src_01.jurisdictions = {};
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { 3,4,5,6,7 };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );

   src_01.jurisdictions = { 3,4,5 };
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { 3,4,5,6,7,8 };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );

   src_01.jurisdictions = { 9 };
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { 7,8 };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );

   src_01.jurisdictions = { 7,8,9 };
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { 7 };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );

   src_01.jurisdictions = { 7 };
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { 7,8 };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );

   src_01.jurisdictions = { 0,1 };
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { 0,1,2,3 };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );

   src_01.jurisdictions = { 0 };
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { 0 };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );

   src_01.jurisdictions = { 0,1,2,3 };
   updater.update( db, src_01 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );
   src_02.jurisdictions = { 1,3,4 };
   updater.update( db, src_02 );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_01 ) );
   BOOST_REQUIRE_EQUAL( true, updater.check_jurisdictions( db, src_02 ) );

} FC_LOG_AND_RETHROW()

BOOST_AUTO_TEST_SUITE_END()
