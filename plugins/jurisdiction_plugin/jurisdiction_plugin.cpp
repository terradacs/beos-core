#include <eosio/jurisdiction_plugin/jurisdiction_plugin.hpp>
#include <eosio/chain/jurisdiction_object.hpp>

namespace eosio {
  static appbase::abstract_plugin& _jurisdiction_plugin = app().register_plugin<jurisdiction_plugin>();

  class jurisdiction_plugin_impl
  {
    public:
      chain_plugin *chain_plug = nullptr;
  };

  jurisdiction_plugin::jurisdiction_plugin() : my(new jurisdiction_plugin_impl())
  {

  }
  
  jurisdiction_plugin::~jurisdiction_plugin()
  {

  }

  void jurisdiction_plugin::set_program_options(options_description& cli, options_description& cfg)
  {

  }

  void jurisdiction_plugin::plugin_initialize(const variables_map& options)
  {
    my->chain_plug = app().find_plugin<chain_plugin>();
  }

  void jurisdiction_plugin::plugin_startup()
  {

  }

  void jurisdiction_plugin::plugin_shutdown() 
  {

  }

  jurisdiction_apis::read_write jurisdiction_plugin::get_read_write_api() const
  {
    controller& c = my->chain_plug->chain();
    return jurisdiction_apis::read_write(c, my->chain_plug->get_abi_serializer_max_time());
  }

  namespace jurisdiction_apis
  {
    read_write::get_producer_jurisdiction_results read_write::get_producer_jurisdiction(const get_producer_jurisdiction_params &producer_name)
    {
      read_write::get_producer_jurisdiction_results ret;
      using namespace eosio::chain;
      try 
      {
        const auto &idx_by_prod = db.db().get_index<chain::jurisdiction_index, chain::by_producer_jurisdiction>();
        auto itr_prod_jur = idx_by_prod.find(producer_name.producer_name);
        if (itr_prod_jur != idx_by_prod.end())
        {
          ret.producer_name = itr_prod_jur->producer;
          ret.jurisdictions.emplace_back(itr_prod_jur->jurisdiction);
        }
      } 
      catch (const fc::exception& e) 
      {
        throw e;
      }
      catch( const std::exception& e ) 
      {
        auto fce = fc::exception(
          FC_LOG_MESSAGE( info, "Caught std::exception: ${what}", ("what",e.what())),
          fc::std_exception_code,
          BOOST_CORE_TYPEID(e).name(),
          e.what()
        );
        throw fce;
      }
      catch( ... ) 
      {
        auto fce = fc::unhandled_exception(
          FC_LOG_MESSAGE( info, "Caught unknown exception"),
          std::current_exception()
        );
        throw fce;
      }
      return ret;
    }

    read_write::get_jurisdictions_results read_write::get_jurisdictions(const get_jurisdictions_params &)
    {
      read_write::get_jurisdictions_results ret;
      using namespace eosio::chain;
      try 
      {
        const auto &idx_by_prod = db.db().get_index<chain::jurisdiction_index, chain::by_producer_jurisdiction>();
        for (auto itr = idx_by_prod.begin(); itr != idx_by_prod.end(); ++itr)
        {
          ret.jurisdictions.emplace(itr->jurisdiction);
        }
      } 
      catch (const fc::exception& e) 
      {
        throw e;
      }
      catch( const std::exception& e ) 
      {
        auto fce = fc::exception(
          FC_LOG_MESSAGE( info, "Caught std::exception: ${what}", ("what",e.what())),
          fc::std_exception_code,
          BOOST_CORE_TYPEID(e).name(),
          e.what()
        );
        throw fce;
      }
      catch( ... ) 
      {
        auto fce = fc::unhandled_exception(
          FC_LOG_MESSAGE( info, "Caught unknown exception"),
          std::current_exception()
        );
        throw fce;
      }
      return ret;
    }
  }
}