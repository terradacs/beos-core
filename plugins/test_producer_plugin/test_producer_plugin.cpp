/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */
#include <eosio/test_producer_plugin/test_producer_plugin.hpp>

namespace eosio {

static appbase::abstract_plugin& _test_producer_plugin = app().register_plugin<test_producer_plugin>();

using eosio::chain::jurisdiction_test_provider;

class test_producer_plugin_impl
{
   public:

      jurisdiction_test_provider::ptr_base test_provider;

      producer_plugin* producer_plug = nullptr;

      test_producer_plugin_impl()
            : test_provider( new jurisdiction_test_provider() )
      {

      }
};

test_producer_plugin::test_producer_plugin()
            :my( new test_producer_plugin_impl() )
{
}

test_producer_plugin::~test_producer_plugin()
{
}

void test_producer_plugin::set_program_options(options_description& cli, options_description& cfg)
{
}

void test_producer_plugin::plugin_initialize(const variables_map& options)
{
  my->producer_plug = app().find_plugin<producer_plugin>();

  my->producer_plug->set_jurisdiction_provider( my->test_provider->getptr() );
}

void test_producer_plugin::plugin_startup()
{
}

void test_producer_plugin::plugin_shutdown()
{
}

test_producer_apis::read_write test_producer_plugin::get_read_write_api()
{
  return test_producer_apis::read_write( my->producer_plug, this );
}

jurisdiction_test_provider::ptr_base test_producer_plugin::get_test_provider()
{
   return my->test_provider;
}

namespace test_producer_apis
{
   template< typename CallMethod >
   read_write::accelerate_results read_write::accelerate_time_internal( const accelerate_time_params& params, CallMethod method )
   {
      try {

         assert( producer_plug );

         fc::microseconds res;

         if( params.type == "s" )
            res = fc::seconds( params.time );
         else if( params.type == "m" )
            res = fc::minutes( params.time );
         else if( params.type == "h" )
            res = fc::hours( params.time );
         else if( params.type == "d" )
            res = fc::days( params.time );
         else
            return accelerate_results( false );

         method( res );

         return accelerate_results( true );

         } catch (const fc::exception& e) {
            throw e;
         } catch( const std::exception& e ) {
            auto fce = fc::exception(
                  FC_LOG_MESSAGE( info, "Caught std::exception: ${what}", ("what",e.what())),
                  fc::std_exception_code,
                  BOOST_CORE_TYPEID(e).name(),
                  e.what()
            );
            throw fce;
         } catch( ... ) {
            auto fce = fc::unhandled_exception(
                  FC_LOG_MESSAGE( info, "Caught unknown exception"),
                  std::current_exception()
            );
            throw fce;
         }

      return accelerate_results( false );
   }

  read_write::accelerate_results read_write::accelerate_time( const accelerate_time_params& params )
  {
      auto call = [this]( const fc::microseconds& res )
      {
         producer_plug->accelerate_time( res );
      };

      return accelerate_time_internal( params, call );
  }

  read_write::accelerate_results read_write::accelerate_mock_time( const accelerate_time_params& params )
  {
      auto call = [this]( const fc::microseconds& res )
      {
         producer_plug->accelerate_mock_time( res );
      };

      return accelerate_time_internal( params, call );
  }

  read_write::accelerate_results read_write::accelerate_blocks( const accelerate_blocks_params& params )
  {
    try {

      assert( producer_plug );
      producer_plug->accelerate_blocks( params.blocks );

      return accelerate_results( true );

      } catch (const fc::exception& e) {
        throw e;
      } catch( const std::exception& e ) {
        auto fce = fc::exception(
            FC_LOG_MESSAGE( info, "Caught std::exception: ${what}", ("what",e.what())),
            fc::std_exception_code,
            BOOST_CORE_TYPEID(e).name(),
            e.what()
        );
        throw fce;
      } catch( ... ) {
        auto fce = fc::unhandled_exception(
            FC_LOG_MESSAGE( info, "Caught unknown exception"),
            std::current_exception()
        );
        throw fce;
      }

    return accelerate_results( false );
  }

   read_write::update_jurisdictions_results read_write::update_jurisdictions( const update_jurisdictions_params& params )
   {

      try {

         assert( producer_plug && test_producer_plug );
         test_producer_plug->get_test_provider()->change( params );

         return update_jurisdictions_results( true );

      } catch (const fc::exception& e) {
         throw e;
      } catch( const std::exception& e ) {
         auto fce = fc::exception(
               FC_LOG_MESSAGE( info, "Caught std::exception: ${what}", ("what",e.what())),
               fc::std_exception_code,
               BOOST_CORE_TYPEID(e).name(),
               e.what()
         );
         throw fce;
      } catch( ... ) {
         auto fce = fc::unhandled_exception(
               FC_LOG_MESSAGE( info, "Caught unknown exception"),
               std::current_exception()
         );
         throw fce;
      }

    return update_jurisdictions_results( false );
   }
}

} // namespace eosio
