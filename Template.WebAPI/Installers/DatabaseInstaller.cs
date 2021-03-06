﻿using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Template.Contracts.V1.Requests;
using Template.Contracts.V1.Responses;
using Template.WebAPI.Interfaces;
using Template.Database;
using Template.Domain;
using Template.Services;

namespace Template.WebAPI.Installers
{
    public class DatabaseInstaller : IInstaller
    {
        public void InstallServices(IServiceCollection services, IConfiguration configuration)
        {
            services.AddDbContext<TemplateContext>(options =>
                options.UseSqlServer(
                    configuration.GetConnectionString("TemplateAPI")));
            services.AddIdentity<User, Role>(options => options.SignIn.RequireConfirmedAccount = true)
                .AddEntityFrameworkStores<TemplateContext>();


            // Auth
            services.AddScoped<IAuthService, AuthService>();

            // User
            services.AddScoped<ICRUDService<UserResponse, UserSearchRequest, UserInsertRequest, UserUpdateRequest>, UserService>();
        }
    }
}