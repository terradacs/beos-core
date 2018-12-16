/**
 *  @file
 *  @copyright defined in eos/LICENSE.txt
 */
#include <eosio/test_producer_plugin/test_producer_plugin.hpp>

namespace eosio {

static appbase::abstract_plugin& _test_producer_plugin = app().register_plugin<test_producer_plugin>();

class test_producer_plugin_impl
{
  public:

    producer_plugin* producer_plug = nullptr;
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
}

void test_producer_plugin::plugin_startup()
{
}

void test_producer_plugin::plugin_shutdown()
{
}

test_producer_apis::read_write test_producer_plugin::get_read_write_api() const
{
  return test_producer_apis::read_write( my->producer_plug );
}

namespace test_producer_apis
{
 
  read_write::accelerate_results read_write::accelerate_time( const accelerate_time_params& params )
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

      producer_plug->accelerate_time( res );

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
}

} // namespace eosio
