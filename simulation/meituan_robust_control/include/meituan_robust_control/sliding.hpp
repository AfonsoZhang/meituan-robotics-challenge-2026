#pragma once
#include <algorithm>
namespace meituan_robust_control {
inline double sliding_feedback(double error, double velocity_error, double rho, double lambda, double phi) {
  return rho * std::clamp((velocity_error+lambda*error)/phi,-1.,1.);
}
}
