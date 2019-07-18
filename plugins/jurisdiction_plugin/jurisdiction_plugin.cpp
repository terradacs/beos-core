#include <eosio/jurisdiction_plugin/jurisdiction_plugin.hpp>

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

  jurisdiction_apis::read_only jurisdiction_plugin::get_read_only_api() const
  {
    controller& c = my->chain_plug->chain();
    return jurisdiction_apis::read_only(c, my->chain_plug->get_abi_serializer_max_time());
  }

  namespace jurisdiction_apis
  {
    read_only::get_producer_jurisdiction_results read_only::get_producer_jurisdiction(const get_producer_jurisdiction_params &prod_jur_params)
    {
      EOS_ASSERT(prod_jur_params.producer_names.size() <= JURISDICTION_QUERY_LIMIT, fc::invalid_arg_exception, "Query size is greater than query limit (${n})", ("n", JURISDICTION_QUERY_LIMIT));
      read_only::get_producer_jurisdiction_results ret;
      std::map<chain::account_name, std::vector<chain::code_jurisdiction> > producer_jurisdictions_map;
      try 
      {
        uint16_t count = 0;
        const auto &idx_by_prod = db.db().get_index<chain::jurisdiction_producer_index, chain::by_producer_jurisdiction>();
        for_each(prod_jur_params.producer_names.begin(), prod_jur_params.producer_names.end(), [&](const std::string &name) {
          auto itr_prod_jur = idx_by_prod.lower_bound(name);
          while (itr_prod_jur != idx_by_prod.end() && itr_prod_jur->producer == name && count < JURISDICTION_QUERY_LIMIT)
          {
            producer_jurisdictions_map[name].emplace_back(itr_prod_jur->jurisdiction);
            ++itr_prod_jur;
            ++count;
          }
        }
        );

        for (auto itr = producer_jurisdictions_map.begin(); itr != producer_jurisdictions_map.end(); ++itr)
        {
          ret.producer_jurisdictions.emplace_back(producer_jurisdiction_api_object(itr->first, itr->second));
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

    read_only::get_active_jurisdictions_results read_only::get_active_jurisdictions(const get_active_jurisdictions_params &params)
    {
      EOS_ASSERT(params.limit <= JURISDICTION_QUERY_LIMIT, fc::invalid_arg_exception, "Invalid value for limit ${s} > ${n}", ("s", params.limit)("n", JURISDICTION_QUERY_LIMIT));
      read_only::get_active_jurisdictions_results ret;
      try 
      {
        const auto &idx_by_prod = db.db().get_index<chain::jurisdiction_producer_index, chain::by_producer_jurisdiction>();
        auto itr = idx_by_prod.begin();
        uint16_t count = 0;
        while (itr != idx_by_prod.end() && count < params.limit)
        {
          ret.jurisdictions.emplace(itr->jurisdiction);
          ++itr;
          ++count;
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

    read_only::get_all_jurisdictions_results read_only::get_all_jurisdictions(const get_all_jurisdictions_params &all_jur_params)
    {
      EOS_ASSERT(all_jur_params.limit <= JURISDICTION_QUERY_LIMIT, fc::invalid_arg_exception, "Invalid value for limit ${s} > ${n}", ("s", all_jur_params.limit)("n", JURISDICTION_QUERY_LIMIT));
      read_only::get_all_jurisdictions_results ret;
      try 
      {
        const auto &idx_by_prod = db.db().get_index<chain::jurisdiction_dictionary_index, chain::by_code_jurisdiction_dictionary>();
        auto itr = all_jur_params.last_code.valid() ? idx_by_prod.find(*all_jur_params.last_code) : idx_by_prod.begin();
        uint16_t count = 0;
        while (itr != idx_by_prod.end() && count < all_jur_params.limit)
        {
          ret.jurisdictions.emplace_back(jurisdiction_api_dictionary_object(*itr));
          ++itr;
          ++count;
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