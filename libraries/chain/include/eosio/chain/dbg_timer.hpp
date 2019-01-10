#pragma once

#include <chrono>
#include <tuple>
#include <utility> 

namespace eosio {
namespace chain {

class dbg_timer
{
   private:

      FILE* pFile = nullptr;

      const char* file_name = "dbg_timer.log";
      std::chrono::steady_clock::time_point begin;

   public:

      template< typename ... PARAMS >
      dbg_timer( std::string format, PARAMS ... params )
      {
         pFile = fopen( file_name ,"a"); fprintf( pFile, format.c_str(), params ... ); fclose( pFile );
         begin = std::chrono::steady_clock::now();
      }

      template< typename ... PARAMS >
      void write( std::string format, PARAMS ... params )
      {
         format = "\n" + format + "\n";
         pFile = fopen( file_name ,"a"); fprintf( pFile, format.c_str(), params ... ); fclose( pFile );
      }

      void end()
      {
         auto count = std::chrono::duration_cast<std::chrono::microseconds>( std::chrono::steady_clock::now() - begin ).count();

         pFile = fopen( file_name ,"a");
         fprintf( pFile, " time[us]: %ld \n", count );
         fclose( pFile );
      }
};

}}
