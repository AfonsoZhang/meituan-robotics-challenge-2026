#include <cassert>
#include <cmath>
#include "meituan_robust_control/sliding.hpp"
int main() {
  using meituan_robust_control::sliding_feedback;
  assert(sliding_feedback(0,0,4,6,.08)==0);
  for(int i=-10000;i<=10000;++i){
    double s=i*.0001;
    double u=sliding_feedback(0,s,4,6,.08);
    assert(std::abs(u)<=4.);
    assert(s*u>=0.);
    assert(std::abs(u+sliding_feedback(0,-s,4,6,.08))<1e-12);
    if(std::abs(s)<.08)assert(std::abs(u-50*s)<1e-12);
  }
  assert(sliding_feedback(.1,0,4,6,.08)==4.);
  assert(sliding_feedback(-.1,0,4,6,.08)==-4.);
}
