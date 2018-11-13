#pragma once
#include <eosiolib/types.h>


#ifdef __cplusplus
extern "C" {
#endif

   /**
    * @brief Get the number of actual block in blockchain
    */
   int tapos_block_num();
   void newaccount();

   ///@ } privilegedcapi

   /**
    *  Defined in distribution_api
    */
   void reward_all(uint64_t, uint64_t, uint64_t, const void*, int, bool);
   void reward_done(const void*, int, bool);

#ifdef __cplusplus
}
#endif


