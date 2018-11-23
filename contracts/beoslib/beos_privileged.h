#pragma once
#include <eosiolib/types.h>


#ifdef __cplusplus
extern "C" {
#endif

struct block_producer_voting_info;

   /**
    * @brief Get the number of actual block in blockchain
    */
   int tapos_block_num();

   ///@ } privilegedcapi

   /**
    *  Defined in distribution_api
    */
   void reward_all(uint64_t, uint64_t, uint64_t, const void*, int, bool, block_producer_voting_info* , uint32_t);
   void reward_done(const void*, int, bool);

#ifdef __cplusplus
}
#endif


