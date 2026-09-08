// Project implementation assisted by OpenAI Codex, 2026-09-08.
// Uses Apache-2.0 ros2_controllers JTC through inheritance, no upstream source copy.
// Boundary-layer sliding feedback inspired by Slotine (1985), DOI 10.1177/027836498500400205.
#include <algorithm>
#include "meituan_robust_control/sliding.hpp"
#include <atomic>
#include <cmath>
#include <memory>
#include <vector>
#include <kdl_parser/kdl_parser.hpp>
#include <kdl/chainfksolverpos_recursive.hpp>
#include <kdl/chainjnttojacsolver.hpp>
#include <joint_trajectory_controller/joint_trajectory_controller.hpp>
#include <pluginlib/class_list_macros.hpp>
#include <std_msgs/msg/float64_multi_array.hpp>

namespace meituan_robust_control {
using CallbackReturn = controller_interface::CallbackReturn;
class GravitySlidingController : public joint_trajectory_controller::JointTrajectoryController {
  struct Body {
    KDL::Chain chain;
    KDL::JntArray q;
    KDL::Jacobian jac;
    KDL::Vector cog;
    double mass;
    std::vector<size_t> map;
    std::unique_ptr<KDL::ChainFkSolverPos_recursive> fk;
    std::unique_ptr<KDL::ChainJntToJacSolver> js;
  };
  std::vector<std::unique_ptr<Body>> bodies_;
  std::vector<double> rho_, lambda_, phi_, limits_, gravity_;
  bool enabled_ = false;
  std::atomic<bool> gravity_on_{false};
  rclcpp::node_interfaces::OnSetParametersCallbackHandle::SharedPtr callback_;
  std::unique_ptr<realtime_tools::RealtimePublisher<std_msgs::msg::Float64MultiArray>> audit_;
  double last_audit_ = -1.;
public:
  CallbackReturn on_init() override {
    auto ret = JointTrajectoryController::on_init();
    if (ret != CallbackReturn::SUCCESS) return ret;
    auto_declare<bool>("robust.enabled", false);
    auto_declare<bool>("robust.gravity_enabled", false);
    auto_declare<std::string>("robust.model_file", "");
    auto_declare<std::vector<double>>("robust.rho", {4,4,3,.3,.15,.05});
    auto_declare<std::vector<double>>("robust.lambda", {6,6,6,6,6,6});
    auto_declare<std::vector<double>>("robust.phi", {.08,.08,.08,.12,.12,.15});
    auto_declare<std::vector<double>>("robust.effort_limits", {49,49,39,9.8,9.8,9.8});
    return CallbackReturn::SUCCESS;
  }
  CallbackReturn on_configure(const rclcpp_lifecycle::State & previous) override {
    auto ret = JointTrajectoryController::on_configure(previous);
    if (ret != CallbackReturn::SUCCESS) return ret;
    auto node = get_node();
    if (params_.command_interfaces != std::vector<std::string>{"effort"}) {
      RCLCPP_ERROR(node->get_logger(), "Robust controller requires effort-only command interface");
      return CallbackReturn::ERROR;
    }
    enabled_ = node->get_parameter("robust.enabled").as_bool();
    gravity_on_ = node->get_parameter("robust.gravity_enabled").as_bool();
    rho_ = node->get_parameter("robust.rho").as_double_array();
    lambda_ = node->get_parameter("robust.lambda").as_double_array();
    phi_ = node->get_parameter("robust.phi").as_double_array();
    limits_ = node->get_parameter("robust.effort_limits").as_double_array();
    for (auto * values : {&rho_, &lambda_, &phi_, &limits_}) {
      if (values->size() != dof_ || std::any_of(values->begin(),values->end(),[](double v){return !std::isfinite(v) || v<=0.;}))
        return CallbackReturn::ERROR;
    }
    KDL::Tree tree;
    if (!kdl_parser::treeFromFile(node->get_parameter("robust.model_file").as_string(), tree))
      return CallbackReturn::ERROR;
    bodies_.clear(); gravity_.assign(dof_,0.);
    for (const auto & entry : tree.getSegments()) {
      auto body = std::make_unique<Body>();
      if (!tree.getChain("base_link",entry.first,body->chain) || body->chain.getNrOfJoints()==0) continue;
      auto inertia = body->chain.getSegment(body->chain.getNrOfSegments()-1).getInertia();
      body->mass=inertia.getMass(); body->cog=inertia.getCOG();
      if (body->mass<=0.) continue;
      for (const auto & segment : body->chain.segments) {
        if (segment.getJoint().getType()==KDL::Joint::None) continue;
        auto it=std::find(params_.joints.begin(),params_.joints.end(),segment.getJoint().getName());
        if (it==params_.joints.end()) return CallbackReturn::ERROR;
        body->map.push_back(std::distance(params_.joints.begin(),it));
      }
      body->q.resize(body->map.size()); body->jac.resize(body->map.size());
      body->fk=std::make_unique<KDL::ChainFkSolverPos_recursive>(body->chain);
      body->js=std::make_unique<KDL::ChainJntToJacSolver>(body->chain);
      bodies_.push_back(std::move(body));
    }
    if (bodies_.empty()) return CallbackReturn::ERROR;
    callback_=node->add_on_set_parameters_callback([this](const std::vector<rclcpp::Parameter> & ps){
      rcl_interfaces::msg::SetParametersResult result; result.successful=true;
      for (const auto & p:ps) {
        if (p.get_name()=="robust.gravity_enabled") {
          if (p.get_type()!=rclcpp::ParameterType::PARAMETER_BOOL) {result.successful=false; return result;}
        } else if (p.get_name().rfind("robust.",0)==0) {result.successful=false;result.reason="Robust gains are frozen after configure";return result;}
      }
      for (const auto & p:ps) if(p.get_name()=="robust.gravity_enabled") gravity_on_=p.as_bool();
      return result;
    });
    audit_=std::make_unique<realtime_tools::RealtimePublisher<std_msgs::msg::Float64MultiArray>>(
        node->create_publisher<std_msgs::msg::Float64MultiArray>("~/robust_audit",10));
    audit_->msg_.data.resize(1+7*dof_);
    RCLCPP_INFO(node->get_logger(),"Effort controller: %zu massive links, sliding=%d",bodies_.size(),enabled_);
    return CallbackReturn::SUCCESS;
  }
  controller_interface::return_type update(const rclcpp::Time & time,const rclcpp::Duration & period) override {
    auto ret=JointTrajectoryController::update(time,period);
    if (ret!=controller_interface::return_type::OK || joint_command_interface_[3].size()!=dof_) return ret;
    std::fill(gravity_.begin(),gravity_.end(),0.);
    if (gravity_on_) for (auto & b:bodies_) {
      for(size_t j=0;j<b->map.size();++j) b->q(j)=state_current_.positions[b->map[j]];
      KDL::Frame frame;
      if(b->fk->JntToCart(b->q,frame)<0 || b->js->JntToJac(b->q,b->jac)<0) return controller_interface::return_type::ERROR;
      KDL::Vector offset=frame.M*b->cog;
      for(size_t j=0;j<b->map.size();++j) {
        auto twist=b->jac.getColumn(j);
        gravity_[b->map[j]]+=b->mass*9.81*(twist.vel+twist.rot*offset).z();
      }
    }
    bool publish=time.seconds()-last_audit_>=.01 && audit_->trylock();
    if(publish)audit_->msg_.data[0]=time.seconds();
    bool valid=true;
    for(size_t i=0;i<dof_;++i) {
      double sliding=state_error_.velocities[i]+lambda_[i]*state_error_.positions[i];
      double robust=enabled_ ? sliding_feedback(state_error_.positions[i],state_error_.velocities[i],rho_[i],lambda_[i],phi_[i]) : 0.;
      auto & command=joint_command_interface_[3][i].get();
      double raw=command.get_value()+gravity_[i]+robust;
      valid=valid && std::isfinite(raw);
      double applied=std::isfinite(raw) ? std::clamp(raw,-limits_[i],limits_[i]) : 0.;
      command.set_value(applied);
      if(publish) {
        audit_->msg_.data[1+i]=gravity_[i];audit_->msg_.data[1+dof_+i]=robust;
        audit_->msg_.data[1+2*dof_+i]=raw;audit_->msg_.data[1+3*dof_+i]=applied;
        audit_->msg_.data[1+4*dof_+i]=state_desired_.positions[i];
        audit_->msg_.data[1+5*dof_+i]=state_current_.positions[i];
        audit_->msg_.data[1+6*dof_+i]=sliding;
      }
    }
    if(publish){audit_->unlockAndPublish();last_audit_=time.seconds();}
    if (!valid) return controller_interface::return_type::ERROR;
    return ret;
  }
};
}
PLUGINLIB_EXPORT_CLASS(meituan_robust_control::GravitySlidingController, controller_interface::ControllerInterface)
